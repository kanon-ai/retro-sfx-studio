#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>
#include "ymfm_misc.h"
#include "ymfm_opl.h"
#include "ymfm_opm.h"
#include "ymfm_opn.h"

struct Event { uint32_t time, reg, value; };
struct Voice { virtual ~Voice() {} virtual void write(unsigned, unsigned)=0; virtual void sample(double*)=0; virtual unsigned rate(unsigned)=0; };
template<class T> struct Chip : Voice, ymfm::ymfm_interface {
    T chip; int kind; typename T::output_data out{};
    Chip(int k): chip(*this), kind(k) { chip.reset(); }
    // ym2149::generate clocks SSG once; ssg_engine::clock expects clock/8.
    // The pinned upstream ym2149::sample_rate divides by 8 a second time.
    unsigned rate(unsigned clock) override { return kind==0 ? clock/8 : chip.sample_rate(clock); }
    void write(unsigned reg,unsigned value) override {
        unsigned port=(reg>>8)*2; chip.write(port,reg&255); chip.write(port+(kind==0?2:1),value);
    }
    void sample(double *v) override {
        chip.generate(&out);
        if(kind==0 || kind==2) { v[0]=0; for(unsigned i=0;i<T::OUTPUTS;i++) v[0]+=out.data[i]; v[1]=v[0]; }
        else if(kind==3) { v[0]=out.data[0]+out.data[2%T::OUTPUTS]; v[1]=out.data[1%T::OUTPUTS]+out.data[2%T::OUTPUTS]; }
        else if(kind==1) { v[0]=0; for(unsigned i=0;i<T::OUTPUTS;i++) v[0]+=out.data[i]; v[1]=v[0]; }
        else { v[0]=out.data[0]; v[1]=out.data[1%T::OUTPUTS]; }
    }
};
void u16(std::ostream& f,unsigned n) { f.put(n&255); f.put((n>>8)&255); }
void u32(std::ostream& f,unsigned n) { u16(f,n); u16(f,n>>16); }
int main(int argc,char**argv) {
    if(argc!=3) return 2;
    std::ifstream in(argv[1]); unsigned kind,clock,frames,count;
    if(!(in>>kind>>clock>>frames>>count) || kind>4 || clock<100000 || clock>16000000 || frames>44100*12 || count>100000) return 3;
    std::vector<Event> events(count); unsigned last=0;
    for(auto &e:events) { if(!(in>>e.time>>e.reg>>e.value)||e.time<last||e.time>frames||e.reg>511||e.value>255) return 4; last=e.time; }
    std::unique_ptr<Voice> voice;
    switch(kind) {
    case 0: voice.reset(new Chip<ymfm::ym2149>(kind)); break;
    case 1: voice.reset(new Chip<ymfm::ym2413>(kind)); break;
    case 2: voice.reset(new Chip<ymfm::ym2203>(kind)); break;
    case 3: voice.reset(new Chip<ymfm::ym2608>(kind)); break;
    case 4: voice.reset(new Chip<ymfm::ym2151>(kind)); break;
    }
    std::ofstream wav(argv[2],std::ios::binary); if(!wav) return 5;
    wav.write("RIFF",4); u32(wav,36+frames*4); wav.write("WAVEfmt ",8); u32(wav,16);
    u16(wav,1); u16(wav,2); u32(wav,44100); u32(wav,176400); u16(wav,4); u16(wav,16); wav.write("data",4); u32(wav,frames*4);
    const double ratio=double(voice->rate(clock))/44100;
    double held[2]={},prev[2]={},dc[2]={}; size_t index=0; uint64_t native=0;
    // Box integration at the chip's native sample rate, then a 20 Hz DC blocker.
    for(unsigned i=0;i<frames;i++) {
        while(index<events.size() && events[index].time<=i) { auto&e=events[index++]; voice->write(e.reg,e.value); }
        double start=i*ratio,end=(i+1)*ratio,pos=start,sum[2]={};
        while(pos<end-1e-9) {
            if(native<=uint64_t(std::floor(pos+1e-9))) { voice->sample(held); native++; }
            double next=std::min(end,double(native)),weight=next-pos;
            for(int c=0;c<2;c++) sum[c]+=held[c]*weight;
            pos=next;
        }
        for(int c=0;c<2;c++) { double x=sum[c]/ratio; dc[c]=x-prev[c]+0.997154*dc[c]; prev[c]=x; int v=int(std::round(dc[c]*0.8)); u16(wav,unsigned(std::max(-32768,std::min(32767,v)))); }
    }
    return wav.good()?0:6;
}

// Small stand-alone per-pixel orthographic depth-buffer rasterizer.
// Mesh triangles are generated only from immutable source CAD tessellations.
// Input: uint32 N and N records {float x,y,z for 3 vertices; uint8 RGB}.
// Output: binary PPM. No changing or solving physical geometry.
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
struct Tri {float p[9]; uint8_t rgb[3]; };
int main(int argc,char **argv){
    if(argc!=5){std::cerr<<"Usage: raster triangles.bin output.ppm width height\n";return 2;}
    int W=std::stoi(argv[3]),H=std::stoi(argv[4]);
    if(W<=0||H<=0||W>5000||H>5000)return 2;
    std::ifstream in(argv[1],std::ios::binary);
    uint32_t n=0;in.read((char*)&n,4);
    if(!in||n>2000000)return 3;
    std::vector<uint8_t> rgb((size_t)W*H*3,248);
    for(size_t i=0;i<rgb.size();i+=3){rgb[i]=250;rgb[i+1]=251;rgb[i+2]=252;}
    std::vector<float> depth((size_t)W*H,-1e30f);
    for(uint32_t idx=0;idx<n;idx++){
        float p[9];uint8_t color[3];
        in.read((char*)p,sizeof(p));in.read((char*)color,3);
        if(!in)return 4;
        float ax=p[0],ay=p[1],bx=p[3],by=p[4],cx=p[6],cy=p[7];
        float area=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax);
        if(std::abs(area)<1e-7f)continue;
        int x0=std::max(0,(int)std::floor(std::min({ax,bx,cx})));
        int x1=std::min(W-1,(int)std::ceil(std::max({ax,bx,cx})));
        int y0=std::max(0,(int)std::floor(std::min({ay,by,cy})));
        int y1=std::min(H-1,(int)std::ceil(std::max({ay,by,cy})));
        float inv=1.0f/area;
        for(int y=y0;y<=y1;y++){
            for(int x=x0;x<=x1;x++){
                float px=x+0.5f, py=y+0.5f;
                float wa=((bx-px)*(cy-py)-(by-py)*(cx-px))*inv;
                float wb=((cx-px)*(ay-py)-(cy-py)*(ax-px))*inv;
                float wc=1.0f-wa-wb;
                if(wa < -0.000001f || wb < -0.000001f || wc < -0.000001f)continue;
                float z=wa*p[2]+wb*p[5]+wc*p[8];
                size_t at=(size_t)y*W+x;
                if(z>depth[at]+0.0000001f){
                    depth[at]=z;
                    rgb[at*3]=color[0];rgb[at*3+1]=color[1];rgb[at*3+2]=color[2];
                }
            }
        }
    }
    std::ofstream out(argv[2],std::ios::binary);
    out<<"P6\n"<<W<<" "<<H<<"\n255\n";
    out.write((char*)rgb.data(),rgb.size());
    if(!out){return 5;}return 0;
}

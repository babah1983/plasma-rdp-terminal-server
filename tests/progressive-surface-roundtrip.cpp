// Regression: the client must receive all pixels when a new surface is created.
#include <freerdp/codec/progressive.h>
#include <freerdp/codec/color.h>
#include <freerdp/codec/region.h>
#include <cstdio>
#include <vector>
int main(int argc,char**) {
    const bool partial=argc>1;
    auto enc=progressive_context_new(TRUE);
    auto dec=progressive_context_new(FALSE);
    unsigned id=1;
    bool ok=true;
    for (auto wh: {std::pair<unsigned,unsigned>{256,192},{384,256},{128,128}}) {
        const auto [w,h]=wh;
        std::vector<BYTE> src(w*h*4,255), dst(w*h*4,0);
        if(progressive_create_surface_context(dec,id,w,h)<0) return 2;
        REGION16 damage, decoded;
        region16_init(&damage);region16_init(&decoded);
        RECTANGLE_16 r={64,64,96,96};
        if(!partial) r={0,0,(UINT16)w,(UINT16)h};
        if(!region16_union_rect(&damage,&damage,&r)) return 2;
        BYTE *compressed=nullptr; UINT32 length=0;
        int rc=progressive_compress(enc,src.data(),src.size(),PIXEL_FORMAT_BGRX32,w,h,w*4,&damage,&compressed,&length);
        if(rc<=0) return 2;
        rc=progressive_decompress(dec,compressed,length,dst.data(),PIXEL_FORMAT_BGRX32,w*4,0,0,&decoded,id,id);
        bool painted=rc>=0;
        for(unsigned y: {0u,h/2,h-1})for(unsigned x: {0u,w/2,w-1})
            for(unsigned c=0;c<3;c++) painted &= dst[(y*w+x)*4+c]>200;
        std::printf("surface=%u size=%ux%u decode=%d corners_painted=%d policy=%s\n",id,w,h,rc,painted,partial?"old-partial":"full-first-frame");
        ok &= painted;
        progressive_delete_surface_context(dec,id++);
        region16_uninit(&damage);region16_uninit(&decoded);
    }
    progressive_context_free(dec);progressive_context_free(enc);
    return ok?0:1;
}

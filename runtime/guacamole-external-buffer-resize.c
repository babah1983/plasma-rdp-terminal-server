/* Guacamole 1.6.0 lab compatibility fix. Keep external-buffer replacement
 * visible to the rendering plan before its last-frame snapshot is replaced.
 * Uses only the public raw-context API; no internal libguac ABI access. */
#define _GNU_SOURCE
#include <guacamole/display.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <stdio.h>
static _Thread_local struct {
    guac_display_layer *layer;
    unsigned char *buffer;
    size_t stride;
    guac_rect bounds;
} opened;
guac_display_layer_raw_context* guac_display_layer_open_raw(guac_display_layer *layer) {
    guac_display_layer_raw_context* (*fn)(guac_display_layer*);
    *(void**)(&fn)=dlsym(RTLD_NEXT,"guac_display_layer_open_raw");if(!fn)abort();
    guac_display_layer_raw_context *c=fn(layer);
    opened.layer=layer;opened.buffer=c->buffer;opened.stride=c->stride;opened.bounds=c->bounds;
    return c;
}
void guac_display_layer_close_raw(guac_display_layer *layer,guac_display_layer_raw_context *c) {
    void (*fn)(guac_display_layer*,guac_display_layer_raw_context*);
    *(void**)(&fn)=dlsym(RTLD_NEXT,"guac_display_layer_close_raw");if(!fn)abort();
    if(c->buffer && opened.layer==layer &&
       (opened.buffer!=c->buffer || opened.stride!=c->stride ||
        opened.bounds.right!=c->bounds.right || opened.bounds.bottom!=c->bounds.bottom)) {
        c->dirty=c->bounds;
        fprintf(stderr,"KDE lab: invalidate replacement buffer %dx%d\n",c->bounds.right,c->bounds.bottom);
    }
    opened.layer=NULL;
    fn(layer,c);
}

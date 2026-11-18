/* Regression against real libguac: replacing an externally maintained image
 * must invalidate all its pixels, while unchanged geometry stays incremental. */
#include <guacamole/client.h>
#include <guacamole/display.h>
#include <stdlib.h>
#include <stdio.h>
int main(void) {
    guac_client *client=guac_client_alloc();
    if(!client)return 2;
    guac_display *display=guac_display_alloc(client);
    if(!display)return 2;
    guac_display_layer *layer=guac_display_default_layer(display);
    int ok=1;
    unsigned char *external=NULL;
    for(int step=0;step<3;step++) {
        int w=step==1?384:256,h=step==1?256:192;
        unsigned char *next=calloc((size_t)w*h,4);
        if(!next)return 2;
        guac_display_layer_raw_context *c=guac_display_layer_open_raw(layer);
        c->buffer=next;c->stride=w*4;
        c->bounds=(guac_rect){0,0,w,h};
        guac_display_layer_close_raw(layer,c);
        int full=c->dirty.left==0&&c->dirty.top==0&&c->dirty.right==w&&c->dirty.bottom==h;
        printf("replace=%dx%d full_invalidation=%d\n",w,h,full);ok&=full;
        free(external);external=next;
        c=guac_display_layer_open_raw(layer);
        c->dirty=(guac_rect){16,16,32,32};
        guac_display_layer_close_raw(layer,c);
        int incremental=c->dirty.left==16&&c->dirty.top==16&&c->dirty.right==32&&c->dirty.bottom==32;
        printf("unchanged=%dx%d incremental=%d\n",w,h,incremental);ok&=incremental;
    }
    guac_display_stop(display);
    guac_display_free(display);guac_client_free(client);free(external);
    return ok?0:1;
}

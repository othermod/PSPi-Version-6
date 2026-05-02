//-------------------------------------------------------------------------
// flags for vc_dispmanx_element_change_attributes
//
// can be found in interface/vmcs_host/vc_vchi_dispmanx.h
// but you can't include that file as
// interface/peer/vc_vchi_dispmanx_common.h is missing.
//
//-------------------------------------------------------------------------

#ifndef ELEMENT_CHANGE_H
#define ELEMENT_CHANGE_H

#ifndef ELEMENT_CHANGE_LAYER
#define ELEMENT_CHANGE_LAYER (1<<0)
#endif

#ifndef ELEMENT_CHANGE_OPACITY
#define ELEMENT_CHANGE_OPACITY (1<<1)
#endif

#ifndef ELEMENT_CHANGE_DEST_RECT
#define ELEMENT_CHANGE_DEST_RECT (1<<2)
#endif

#ifndef ELEMENT_CHANGE_SRC_RECT
#define ELEMENT_CHANGE_SRC_RECT (1<<3)
#endif

#ifndef ELEMENT_CHANGE_MASK_RESOURCE
#define ELEMENT_CHANGE_MASK_RESOURCE (1<<4)
#endif

#ifndef ELEMENT_CHANGE_TRANSFORM
#define ELEMENT_CHANGE_TRANSFORM (1<<5)
#endif

#endif

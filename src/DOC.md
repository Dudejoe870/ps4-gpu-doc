# PS4-GPU-DOC

**DRAFT 0.2.0**

**--INFORMATION MAY BE INACCURATE, IF IT APPEARS TO BE PLEASE OPEN AN ISSUE [HERE](https://github.com/Dudejoe870/ps4-gpu-doc/issues)--**

## Table of Contents

- [PS4-GPU-DOC](#ps4-gpu-doc)
  - [Table of Contents](#table-of-contents)
  - [1. Introduction](#1-introduction)
    - [1.1 What is the PS4s GPU Anyway](#11-what-is-the-ps4s-gpu-anyway)
    - [1.2 Where Did You Find This Out Anyhow](#12-where-did-you-find-this-out-anyhow)
      - [1.2.1 Meet Your PAL](#121-meet-your-pal)
      - [1.2.2 XGL](#122-xgl)
    - [1.3 So Why Mention All of This](#13-so-why-mention-all-of-this)
  - [2. Orbis OS](#2-orbis-os)
  - [3. PM4](#3-pm4)
    - [3.1 Commands](#31-commands)
  - [4. Registers](#4-registers)
    - [4.1 Context Registers](#41-context-registers)
      - [4.1.1 VGTMultiPrimIbResetEn](#411-vgtmultiprimibreseten)
      - [4.1.2 VGTMultiPrimIbResetIndx](#412-vgtmultiprimibresetindx)
      - [4.1.3 DBDepthControl](#413-dbdepthcontrol)
      - [4.1.4 DBStencilControl](#414-dbstencilcontrol)
      - [4.1.5 CBBlend(0-7)Control](#415-cbblend0-7control)
    - [4.2 Config Registers](#42-config-registers)
      - [4.2.1 VGTPrimitiveType](#421-vgtprimitivetype)
    - [4.3 Shader Persistent Registers](#43-shader-persistent-registers)
  - [5. Events](#5-events)
  - [6. GNM](#6-gnm)
    - [6.1 API Functions](#61-api-functions)
      - [6.1.1 sceGnmSubmitCommandBuffers](#611-scegnmsubmitcommandbuffers)
      - [6.1.2 sceGnmSubmitCommandBuffersForWorkload](#612-scegnmsubmitcommandbuffersforworkload)
  - [Special Thanks](#special-thanks)

<div class="page"/>

## 1. Introduction

This document contains information on the PS4s GPU, more specifically the higher-level components of it. All information comes from publicly available sources and my own reverse engineering of the PS4s firmware 9.0.0 version of the GNM driver (the Graphics API the PS4 uses to issue commands to the GPU, like OpenGL, Direct-X, or Vulkan).

The hope is that this documentation will lead to furthering of Homebrew applications on the PS4, and hopefully emulation (of which I think there is a *lot* of potential for).

### 1.1 What is the PS4s GPU Anyway

The PS4 pro GPU is an AMD GPU based off of the Radeon GCN 4 Polaris 10 (Ellesmere) architecture<sup>1</sup> <sup>2</sup>. The GCN architecture is the underlying specification the hardware is based off of, though surprisingly isn't very important to this document except for shader machine-code, as the [GCN ISA](http://developer.amd.com/wordpress/media/2013/12/AMD_GCN3_Instruction_Set_Architecture_rev1.1.pdf)<sup>3</sup> (Instruction Set Architecture) is needed to understand it.

>1\. The original PS4s GPU actually is based off GCN 1.1, but from here on out all of the information is assuming the PS4 pros GPU (The distinction doesn't matter much for this higher-level document)

> 2\. I'm actually not sure exactly if it was precisely Polaris 10 or maybe some slightly modified version, but the distinction is irrelevant as, if there are any changes, they are purely hardware based and doesn't change the software at all.

> 3\. The link is actually to the GCN 3 ISA, but it's mostly the same to GCN 4, there just isn't a version of the documentation that documents GCN 4 specifically, as all of the changes are hardware optimizations and not actual ISA changes.

### 1.2 Where Did You Find This Out Anyhow

You may be asking yourself, how do you even reverse engineer something as *complicated* as a relatively modern GPU that has so many moving parts no single engineer that even worked on the damn thing probably knows how the entire design interconnects and works with itself. Well the answer is simple really... AMD *told* me how it works. No really. I'm not even breaching any NDAs or anything like that. AMD is actually a fairly notoriously open-source company, and so I'd like you to meet someone who will be helping significantly with this documentation...

<div class="page"/>

#### 1.2.1 Meet Your PAL

The [Platform Abstraction Library](https://github.com/GPUOpen-Drivers/pal)... rolls right off the tounge doesn't it? Okay I'll be honest, this is actually only *one* part to a broader open-source driver that actually is the *real* documentation. I just couldn't resist the play on words. PAL, however, is an essential part to that driver, as it explains how many components of the GPU works including the things that get submitted to the lower-level driver that interacts with the GPU via PCI-E directly, like the [PM4 format command buffers](https://developer.amd.com/wordpress/media/2013/10/si_programming_guide_v2.pdf). Coincidentally also what the PS4s own GNM API directly submits to the GPU. However that isn't enough sometimes to figure out everything, at that point it might be useful to look at something that *uses* PAL to implement a well known API... say... Vulkan?

#### 1.2.2 XGL

That's where [XGL](https://github.com/GPUOpen-Drivers/xgl) comes in. XGL is an implementation of the Vulkan API, using PAL as an abstraction over the hardware. However, crucially, PAL is similar in abstraction scope to GNM, the PS4s API. Thus a lot of what you can learn about how PAL is used, will teach you about how GNM is used. And the best part is, XGL is an implementation of the *full* Vulkan API, meaning that everything that games will pretty much ever use, is right there.

> Note: One more thing I'd like to fit in here. Another invaluable tool is the [Radeon GPU Analyzer](https://github.com/GPUOpen-Tools/radeon_gpu_analyzer) software, it allows you to write GLSL and translate it directly into GCN machine-code, allowing you to see exactly how it works. Can be useful for generally just figuring out where certain GCN instructions are used where.

### 1.3 So Why Mention All of This

Because I don't want this document to just be about the technical information I've gathered (though we'll get to that part shortly), but also about *how* to look for the information I've gathered. So that hopefully collaboration can improve documentation over time, and correct errors that I've made in my own research.

Nothing I'm presenting here is necessarily ground-breaking or new, anyone could've figured this stuff out pretty easily. But I am the first (I think?) to put it all in one place that is easily accessible and maintainable when new information gets discovered.

<div class="page" />

## 2. Orbis OS

The PS4s operating system is named Orbis, but it's actually based off FreeBSD 9.0, thus most of its functionality you can expect is very POSIX like.

The OS is split up into different libraries, \*.prx files. Well actually \*.sprx files before decryption that are signed and can only be decoded using a PS4 (at time of writing). But really \*.prx files are just ELF (Executable Linkable Format) files, a well documented format that needs no introduction.

We won't go too in-depth into the OS in this document, basically the only library we care about is `libSceGnmDriver.sprx`<sup>1</sup> (And the libraries that support that one, but most of the calls it makes are just standard library stuff).

> 1\. There are actually two versions of this library. One for the Original PS4 / Slim, and one for "Neo mode" aka the PS4 pro. The version I reverse engineered was the PS4 pro version.

<div class="page"/>

## 3. PM4

PM4 is the format that the PS4 uses for its Command Buffers. The format consists of packets of data, which are essentially commands that tell the GPU to do things like change the current state of the GPU, and draw geometry, even instancing and compute are supported.

### 3.1 Commands

This actually won't be a long section as all the documentation you need is right [here](https://developer.amd.com/wordpress/media/2013/10/si_programming_guide_v2.pdf)<sup>1</sup>, it'd also be advisable to look at the [XGL](https://github.com/GPUOpen-Drivers/xgl) source code to see what the commands are used for. However one thing that the PM4 document doesn't tell you is all the opcodes for the commands listed in it (for some reason). So here they are. (Taken from public sources)

| Name                        | Opcode |
|-----------------------------|--------|
| NOP                         | 0x10   |
| SET_BASE                    | 0x11   |
| CLEAR_STATE                 | 0x12   |
| INDEX_BUFFER_SIZE           | 0x13   |
| DISPATCH_DIRECT             | 0x15   |
| DISPATCH_INDIRECT           | 0x16   |
| ATOMIC_GDS                  | 0x1D   |
| ATOMIC                      | 0x1E   |
| OCCLUSION_QUERY             | 0x1F   |
| SET_PREDICATION             | 0x20   |
| COND_EXEC                   | 0x22   |
| PRED_EXEC                   | 0x23   |
| DRAW_INDIRECT               | 0x24   |
| DRAW_INDEX_INDIRECT         | 0x25   |
| INDEX_BASE                  | 0x26   |
| DRAW_INDEX_2                | 0x27   |
| CONTEXT_CONTROL             | 0x28   |
| INDEX_TYPE                  | 0x2A   |
| DRAW_INDIRECT_MULTI         | 0x2C   |
| DRAW_INDEX_AUTO             | 0x2D   |
| DRAW_INDEX_IMMED<sup>2</sup>| 0x2E   |
| NUM_INSTANCES               | 0x2F   |
| DRAW_INDEX_MULTI_AUTO       | 0x30   |
| INDIRECT_BUFFER_CONST       | 0x33   |
| STRMOUT_BUFFER_UPDATE       | 0x34   |
| DRAW_INDEX_OFFSET_2         | 0x35   |
| WRITE_DATA                  | 0x37   |
| DRAW_INDEX_INDIRECT_MULTI   | 0x38   |
| MEM_SEMAPHORE               | 0x39   |
| MPEG_INDEX<sup>2</sup>      | 0x3A   |
| COPY_DW                     | 0x3B   |
| WAIT_REG_MEM                | 0x3C   |
| MEM_WRITE<sup>2</sup>       | 0x3D   |
| INDIRECT_BUFFER             | 0x3F   |
| COPY_DATA                   | 0x40   |
| PFP_SYNC_ME                 | 0x42   |
| SURFACE_SYNC                | 0x43   |
| ME_INITIALIZE<sup>2</sup>   | 0x44   |
| COND_WRITE                  | 0x45   |
| EVENT_WRITE                 | 0x46   |
| EVENT_WRITE_EOP             | 0x47   |
| EVENT_WRITE_EOS             | 0x48   |
| PREAMBLE_CNTL               | 0x4A   |
| ONE_REG_WRITE<sup>2</sup>   | 0x57   |
| LOAD_SH_REG                 | 0x5F   |
| LOAD_CONFIG_REG             | 0x60   |
| LOAD_CONTEXT_REG            | 0x61   |
| SET_CONFIG_REG              | 0x68   |
| SET_CONTEXT_REG             | 0x69   |
| SET_CONTEXT_REG_INDIRECT    | 0x73   |
| SET_SH_REG                  | 0x76   |
| SET_SH_REG_OFFSET           | 0x77   |
| LOAD_CONST_RAM              | 0x80   |
| WRITE_CONST_RAM             | 0x81   |
| DUMP_CONST_RAM              | 0x83   |
| INCREMENT_CE_COUNTER        | 0x84   |
| INCREMENT_DE_COUNTER        | 0x85   |
| WAIT_ON_CE_COUNTER          | 0x86   |
| WAIT_ON_DE_COUNTER          | 0x87   |
| WAIT_ON_DE_COUNTER_DIFF     | 0x88   |

Any not listed are unknown at this time and will be updated as more information is gathered.

> 1\. Here's a [mirror](https://www.x.org/docs/AMD/old/si_programming_guide_v2.pdf) just incase the original link goes down.

> Note: Unless otherwise specified values are from PAL [si_ci_vi_merged_pm4_it_opcodes.h](https://github.com/GPUOpen-Drivers/pal/blob/dev/src/core/hw/gfxip/gfx6/chip/si_ci_vi_merged_pm4_it_opcodes.h)

> 2\. Taken from [Mesa3d source code](https://github.com/mesa3d/mesa/blob/main/src/amd/common/sid.h)

<div class="page"/>

## 4. Registers

 There are so many we can't hope to list them all but the ones that are listed here are the important ones that have been figured out their meaning and how to use them. For the full list look [here](https://github.com/GPUOpen-Drivers/pal/blob/dev/src/core/hw/gfxip/gfx6/chip/si_ci_vi_merged_offset.h).

<div class="page"/>

### 4.1 Context Registers

Context registers are present at offset `0xA000`.

#### 4.1.1 VGTMultiPrimIbResetEn

<img src="svgs/context/VGT_MULTI_PRIM_IB_RESET_EN.svg">

- RESET_EN (EN): If set to one, this bit enables Primitive restarting.

Register Offset: `0x2A5`

Description: Enables Primitive restarting. See [here](https://www.khronos.org/opengl/wiki/Vertex_Rendering#Common) if you want to know what that is.

<div class="page"/>

#### 4.1.2 VGTMultiPrimIbResetIndx

<img src="svgs/context/VGT_MULTI_PRIM_IB_RESET_INDX.svg">

- RESET_INDX: The Primitive restart index.

Register Offset: `0x103`

Description: Defines the index that, when placed in the meshes indices, restarts drawing the mesh at that point in the indices. See [here](https://www.khronos.org/opengl/wiki/Vertex_Rendering#Common) for information on Primitive restarting.

<div class="page"/>

#### 4.1.3 DBDepthControl

<img src="svgs/context/DB_DEPTH_CONTROL.svg">

- STENCIL_ENABLE (EN0): Enables Stencil testing.
- Z_ENABLE (EN1): Enables Z-Buffering.
- Z_WRITE_ENABLE (EN2): Enables writing to the Z-Buffer.
- DEPTH_BOUNDS_ENABLE (EN3): Enables Depth Bounds (A minimum and maximum depth value).
- ZFUNC: The Depth Compare function to use.
  - NEVER: `0x00`
  - LESS: `0x01`
  - EQUAL: `0x02`
  - LEQUAL: `0x03`
  - GREATER: `0x04`
  - NOT_EQUAL: `0x05`
  - GEQUAL: `0x06`
  - ALWAYS: `0x07`
- BACKFACE_ENABLE (EN4): Not exactly sure 100%, but perhaps it enables Stencil testing on backfaces? Regardless, apparently this is supposed to be always on.<sup>1</sup>
- STENCILFUNC (SFUNC): The Stencil compare function to use on the Stencil reference value.
  - NEVER: `0x00`
  - LESS: `0x01`
  - EQUAL: `0x02`
  - LEQUAL: `0x03`
  - GREATER: `0x04`
  - NOT_EQUAL: `0x05`
  - GEQUAL: `0x06`
  - ALWAYS: `0x07`
- STENCILFUNC_BF: The Stencil compare function to use on the Stencil reference value for backfaces.
  - NEVER: `0x00`
  - LESS: `0x01`
  - EQUAL: `0x02`
  - LEQUAL: `0x03`
  - GREATER: `0x04`
  - NOT_EQUAL: `0x05`
  - GEQUAL: `0x06`
  - ALWAYS: `0x07`
- ENABLE_COLOR_WRITES_ON_DEPTH_FAIL (EN5): Unknown what this is for<sup>1</sup>, always set to `0` in PAL.
- DISABLE_COLOR_WRITES_ON_DEPTH_PASS (EN6): Unknown what this is for<sup>1</sup>, always set to `0` in PAL.

Register Offset: `0x200`

Description: Controls all sorts of functionality relating to the Depth buffer and Stencil buffer.

> 1\. According to [PAL source code](https://github.com/GPUOpen-Drivers/pal/blob/dev/src/core/hw/gfxip/gfx6/gfx6DepthStencilState.cpp) (Look for `void DepthStencilState::Init`)

<div class="page"/>

#### 4.1.4 DBStencilControl

<img src="svgs/context/DB_STENCIL_CONTROL.svg">

- Stencil Operation Values:
  - KEEP: `0x00`
  - ZERO: `0x01`
  - REPLACE_TEST: `0x02`
  - ADD_CLAMP: `0x03`
  - SUB_CLAMP: `0x04`
  - INVERT: `0x05`
  - ADD_WRAP: `0x06`
  - SUB_WRAP: `0x07`

- STENCILFAIL (S_FAIL): Stencil operation to use in the Stencil fail case.
  - See Stencil Operation Values.
- STENCILZPASS (S_ZPASS): Stencil operation to use in the Z-buffer pass case.
  - See Stencil Operation Values.
- STENCILZFAIL (S_ZFAIL): Stencil operation to use in the Z-buffer fail case.
  - See Stencil Operation Values.
- STENCILFAIL_BF (S_FAIL_BF): Stencil operation to use in the Stencil fail case on backfaces.
  - See Stencil Operation Values.
- STENCILZPASS_BF (S_ZPASS_BF): Stencil operation to use in the Z-buffer pass case on backfaces.
  - See Stencil Operation Values.
- STENCILZFAIL_BF (S_ZFAIL_BF): Stencil operation to use in the Z-buffer fail case on backfaces.
  - See Stencil Operation Values.

Register Offset: `0x10B`

Description: Controls all of the Stencil operations to use in various cases.

<div class="page"/>

#### 4.1.5 CBBlend(0-7)Control

<img src="svgs/context/CB_BLEND0_7_CONTROL.svg">

- Blend Operation Values:
  - ZERO: `0x00`
  - ONE: `0x01`
  - SRC_COLOR: `0x02`
  - ONE_MINUS_SRC_COLOR: `0x03`
  - DST_COLOR: `0x04`
  - ONE_MINUS_DST_COLOR: `0x05`
  - SRC_ALPHA: `0x06`
  - ONE_MINUS_SRC_ALPHA: `0x07`
  - DST_ALPHA: `0x08`
  - ONE_MINUS_DST_ALPHA: `0x09`
  - CONSTANT_COLOR: `0x0A`
  - ONE_MINUS_CONSTANT_COLOR: `0x0B`
  - CONSTANT_ALPHA: `0x0C`
  - ONE_MINUS_CONSTANT_ALPHA: `0x0D`
  - SRC_ALPHA_SATURATE: `0x0E`
  - SRC1_COLOR: `0x0F` (For Dual-source Blending)
  - ONE_MINUS_SRC1_COLOR: `0x10` (For Dual-source Blending)
  - SRC1_ALPHA: `0x11` (For Dual-source Blending)
  - ONE_MINUS_SRC1_ALPHA: `0x12` (For Dual-source Blending)

- Blend Function Values:
  - DST_PLUS_SRC: `0x00`
  - SRC_MINUS_DST: `0x01`
  - DST_MINUS_SRC: `0x02`
  - MIN_DST_SRC: `0x03`
  - MAX_DST_SRC: `0x04`

- COLOR_SRCBLEND: Color source Blend Operation.
  - See Blend Operation Values.
- COLOR_COMB_FCN (COLOR_C_FCN): Color Blend Function.
  - See Blend Function Values.
- COLOR_DESTBLEND: Color destination Blend Operation.
  - See Blend Operation Values.
- ALPHA_SRCBLEND: Alpha source Blend Operation.
  - See Blend Operation Values.
- ALPHA_COMB_FCN (ALPHA_C_FCN): Alpha Blend Function.
  - See Blend Function Values.
- ALPHA_DESTBLEND: Alpha destination Blend Operation.
  - See Blend Operation Values.
- SEPARATE_ALPHA_BLEND (EN0): Enables whether or not to separate Blending operations between Color and Alpha.<sup>1</sup>
- ENABLE (EN): Enables Blending for this Render Target.<sup>1</sup>
- DISABLE_ROP3 (EN1): Unknown at this time.

Register Offsets: `0x1E0`-`0x1E7`

Description: Sets the Blending operations and functions for all 8 Render Targets. Supports [Dual-source Blending](https://www.khronos.org/opengl/wiki/Blending#Dual_Source_Blending). Dual-source Blending only works on Targets 0 with the second source being Target 1.<sup>2</sup>

> 1\. This is an educated guess.

> 2\. See [here](https://github.com/GPUOpen-Drivers/pal/blob/dev/src/core/hw/gfxip/gfxDevice.cpp) `bool GfxDevice::CanEnableDualSourceBlend` to find out more about the requirements for Dual-source blending.

<div class="page"/>

### 4.2 Config Registers

Config registers are present at offset `0x2000`.

#### 4.2.1 VGTPrimitiveType

<img src="svgs/config/VGT_PRIMITIVE_TYPE.svg">

- PRIM_TYPE: The Primitive type to render when submitting Draw Calls
  - POINT_LIST: `0x00`
  - LINE_LIST: `0x01`
  - LINE_STRIP: `0x02`
  - TRIANGLE_LIST: `0x03`
  - TRIANGLE_STRIP: `0x04`
  - RECT_LIST: `0x05`
  - QUAD_LIST: `0x06`
  - QUAD_STRIP: `0x07`
  - LINE_LIST_ADJ: `0x08`
  - LINE_STRIP_ADJ: `0x09`
  - TRIANGLE_LIST_ADJ: `0x0A`
  - TRIANGLE_STRIP_ADJ: `0x0B`
  - PATCH: `0x0C`
  - TRIANGLE_FAN: `0x0D`
  - LINE_LOOP: `0x0E`
  - POLYGON: `0x0F`
  - TWOD_RECT_LIST: `0x10`

Register Offset: `0x256`

Description: Describes the Primitive type to use when rendering geometry.

<div class="page"/>

### 4.3 Shader Persistent Registers

**TODO**

<div class="page"/>

## 5. Events

**TODO**

<div class="page"/>

## 6. GNM

The GNM API is the API used by the PS4 to abstract over the lower-level device driver (which it issues commands to via the ioctl function), think of it as like OpenGL, Direct-X, or Vulkan. However unlike those APIs, GNM is a bit lower-level, actually low-level enough to give games higher-level driver-like control over the GPU.

> Note: Quick note about GNMX. You may have heard about GNMX as an even higher-level API, well unfortunately there's not much we can do to get information about that API as it seems to be statically linked within games. Thus there is no information about function names or anything of the sort. But luckily that doesn't really matter as GNMX just boils down to calling GNM functions, so we can safely ignore it.

<div class="page"/>

### 6.1 API Functions

All functions are currently untested on real hardware. All information is purely based off decompiled code from 9.0.0 firmware.

> Note: All function names come from the names embedded in the ELF file. Some parameter names come from error messages embedded in the code.

#### 6.1.1 sceGnmSubmitCommandBuffers

```c
int __stdcall sceGnmSubmitCommandBuffers(uint32_t length, 
    void* dcbGpuAddrs[], uint32_t dcbSizesInBytes[], 
    void* ccbGpuAddrs[], uint32_t ccbSizesInBytes[]);
```

- length: The amount of Command Buffers (for both the DE and CE) to submit.
- dcbGpuAddrs: A list of pointers to the addresses of the Command Buffers to submit to the DE. (Cannot be null)
- dcbSizesInBytes: A list of sizes of each Command Buffer to submit to the DE. (Cannot be null)
- ccbGpuAddrs: A list of pointers to the addresses of the Command Buffers to submit to the CE. (Can be null)
- ccbSizesInBytes: A list of sizes of each Command Buffer to submit to the CE. (Can be null if ccbGpuAddrs is also null)

Description: Submits `length` amount of Command Buffers to the DE (Draw Engine), and optionally the CE (Constant Engine).

Returns: `0` if successful. Otherwise it returns some other value (Error codes not documented yet)

Exceptions: Unknown at this time.

<div class="page"/>

#### 6.1.2 sceGnmSubmitCommandBuffersForWorkload

```c
int __stdcall sceGnmSubmitCommandBuffersForWorkload(
    uint32_t unused, uint32_t length, 
    void* dcbGpuAddrs[], uint32_t dcbSizesInBytes[], 
    void* ccbGpuAddrs[], uint32_t ccbSizesInBytes[])
```

Description: Same as `sceGnmSubmitCommandBuffers` but with an unused parameter. Perhaps was used for debugging on Devkit firmware? Complete speculation. `sceGnmSubmitCommandBuffers` actually just directly calls this function with the length parameter copied to the unused parameter.

<div class="page"/>

## Special Thanks

- [Inori](https://github.com/Inori) developer of [GPCS4](https://github.com/Inori/GPCS4) for writing nice and readable code :)
- The NSA for open-sourcing [Ghidra](https://github.com/NationalSecurityAgency/ghidra), the reverse-engineering tool. And to all the developers who have now contributed to the project.
- AMD for open-sourcing some of their [Radeon drivers](https://github.com/GPUOpen-Drivers/AMDVLK) which helped immensely with learning the hardware.
- The [Mesa](https://github.com/mesa3d/mesa) developers for also writing quite nice and readable code :)
- The Wavedrom developers for the wonderful [bitfield SVG renderer](https://github.com/wavedrom/bitfield).
- [yzane](https://github.com/yzane) for the [Markdown PDF](https://github.com/yzane/vscode-markdown-pdf) Visual Studio Code extension.

/* mbed Microcontroller Library
 * Copyright (c) 2018 ARM Limited
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef MBED_MBED_RTX_H
#define MBED_MBED_RTX_H

#include <stdint.h>

#if defined(TARGET_GD32F307VG)

#ifndef INITIAL_SP
#define INITIAL_SP              (0x20018000UL)
#endif

#endif

#if (defined(__GNUC__) && !defined(__CC_ARM) && !defined(__ARMCC_VERSION) && defined(TWO_RAM_REGIONS))
extern uint32_t               __StackLimit[];
extern uint32_t               __StackTop[];
extern uint32_t               __end__[];
extern uint32_t               __HeapLimit[];
#define HEAP_START            ((unsigned char*)__end__)
#define HEAP_SIZE             ((uint32_t)((uint32_t)__HeapLimit - (uint32_t)HEAP_START))
#define ISR_STACK_START       ((unsigned char*)__StackLimit)
#define ISR_STACK_SIZE        ((uint32_t)((uint32_t)__StackTop - (uint32_t)__StackLimit))
#endif

#endif  /* MBED_MBED_RTX_H */

#!/usr/bin/env python3
import intelhex

uop = {
    "UCC_COND_CLR": 0,  # Reset uCode counter if jump condition is not met.
    "UCC_CLR": 1,       # Reset uCode counter
    "PC_INC": 2,        # Increment PC
    "PC_WR_ADDR": 3,    # Write PC to address bus
    "PC_RD_ADDR": 4,    # Load address bus into PC 
    "IR0_RD_DB": 5,     # Instruction Register 0 read Data Bus
    "IR1_RD_DB": 6,     # Instruction Register 1 read Data Bus
    "IR2_RD_DB": 7,     # Instruction Register 2 read Data Bus
    "PCL_RD_DB": 8,     # Program Counter Lower (byte) read Data Bus
    "PCH_RD_DB": 9,     # Program Counter High (byte) read Data Bus
    "RD_RD_DB": 10,     # Register Destination read Data Bus
    "RD_DB": 11,        # Read Data Bus
    "WR_DB": 12,
    "SPL_RD_DB": 13,    # Stack Pointer Lower (byte) read Data Bus
    "SPH_RD_DB": 14,    # Stack Pointer High (byte) read Data Bus
    "SP_WR_ADDR": 15,   # Stack Pointer write Address Bus
    "SP_INC": 16,       # Stack Pointer Increase
    "SP_DEC": 17,       # Stack Pointer Decrease
    "RS_BUFFER": 18,    # Register Sources buffer (do this before RD_RD_DB)
    "RS_WR_ADDR": 19,   # Register Sources write Address Bus
    "RS+1_WR_ADDR": 20, # RS+1 write Address Bus

    "ALU_WR_FLAG":  29, # ALU write Flag Register

    "MEM_WE": 30,       # External memory write enable
    "MEM_OE": 31,       # External memory output enable
}

write_device = {
    "none": 0b0000,
    "pcl": 0b0001,
    "pch": 0b0010,
    "spl": 0b0011,
    "sph": 0b0100,
    "rd": 0b0101,
    "rs0": 0b0110,
    "rs1": 0b0111,
    "imm": 0b1000,
    "alu": 0b1001,
}

def generate_microcode(config):
    microcode = {}
    for opcode, steps in config.items():
        for step in range(16):
            address = (opcode << 4) | step  # 4-bit opcode + 4-bit step counter
            if step < len(steps):
                signals = steps[step]
                microcode_word = 0
                write_device_code = 0
                print(f"Generating microcode for opcode 0x{opcode:X} at step {step}: {signals}")
                for signal in signals:
                    print(signal)
                    if signal in uop:
                        microcode_word |= 1 << uop[signal]

                    if signal == "PCL_WR_DB":
                        write_device_code = write_device["pcl"]
                    elif signal == "PCH_WR_DB":
                        write_device_code = write_device["pch"]
                    elif signal == "SPL_WR_DB":
                        write_device_code = write_device["spl"]
                    elif signal == "SPH_WR_DB":
                        write_device_code = write_device["sph"]
                    elif signal == "RD_WR_DB":
                        write_device_code = write_device["rd"]
                    elif signal == "RS0_WR_DB":
                        write_device_code = write_device["rs0"]
                    elif signal == "RS1_WR_DB":
                        write_device_code = write_device["rs1"]
                    elif signal == "IMM_WR_DB":
                        write_device_code = write_device["imm"]
                    elif signal == "ALU_OUT_WR_DB":
                        write_device_code = write_device["alu"]
                    
                microcode_word |= (write_device_code << 21)
                print(f" -> Address: 0x{address:02X}, Microcode: 0b{microcode_word:064b}")
            else:
                microcode_word = 0
            microcode[address] = microcode_word
    return microcode

def write_microcode_to_hex(microcode):
    hex_files = [intelhex.IntelHex() for _ in range(4)]

    for address, microcode_word in microcode.items():
        slices = [(microcode_word >> (8 * i)) & 0xFF for i in range(4)]
        for i in range(4):
            hex_files[i][address] = slices[i]

    for i, hex_file in enumerate(hex_files):
        hex_file.tofile(f"uCode{i}.hex", format='hex')

instructions = {
    0x0: [ # NOP, just fetch next instruction.
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
    ],
    0x1: [ # MOV
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["RS0_WR_DB", "RD_RD_DB", "UCC_CLR"],
    ],
    0x2: [ # LDI
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["IMM_WR_DB", "RD_RD_DB", "UCC_CLR"],
    ],
    0x3: [ # LOAD
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["RS_BUFFER", "RS_WR_ADDR"],
        ["RS_WR_ADDR", "RD_RD_DB", "RD_DB", "MEM_OE", "UCC_CLR"],
    ],
    0x4: [ # STORE
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["RS_BUFFER", "RS_WR_ADDR"],
        ["RS_WR_ADDR", "RD_WR_DB", "WR_DB", "MEM_WE", "UCC_CLR"],
    ],
    0x5: [ # ALU
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["ALU_OUT_WR_DB", "ALU_WR_FLAG", "RD_RD_DB", "UCC_CLR"]
    ],
    0x6: [ # JUMP
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["UCC_COND_CLR", "RS_BUFFER", "RS_WR_ADDR"],
        ["RS_WR_ADDR", "PC_RD_ADDR", "UCC_CLR"],
    ],
    0x7: [ # PUSH
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["SP_INC", "PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["SP_WR_ADDR", "RD_WR_DB", "WR_DB", "MEM_WE", "UCC_CLR"],
    ],
    0x8: [ # POP
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["SP_WR_ADDR", "SP_DEC", "RD_RD_DB", "RD_DB", "MEM_OE", "UCC_CLR"],
    ],
    0x9: [ # LDSP
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["RS0_WR_DB", "SPL_RD_DB"],
        ["RS1_WR_DB", "SPH_RD_DB", "UCC_CLR"],
    ],
    0xC: [ # PUSHPC
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["SP_INC", "PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["SP_INC", "SP_WR_ADDR", "PCL_WR_DB", "WR_DB", "MEM_WE"],
        ["SP_WR_ADDR", "PCH_WR_DB", "WR_DB", "MEM_WE", "UCC_CLR"],
    ],
    0xD: [ # POPPC
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["SP_DEC", "SP_WR_ADDR", "PCH_RD_DB", "RD_DB", "MEM_OE"],
        ["SP_DEC", "SP_WR_ADDR", "PCL_RD_DB", "RD_DB", "MEM_OE", "UCC_CLR"]
    ],
    0xE: [ # CALL
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        # INC PC and SP
        ["PC_INC", "SP_INC"],
        # Push PC
        ["SP_INC", "SP_WR_ADDR", "PCL_WR_DB", "WR_DB", "MEM_WE"],
        ["SP_WR_ADDR", "PCH_WR_DB", "WR_DB", "MEM_WE"],
        # Call
        ["RS0_WR_DB", "PCL_RD_DB"],
        ["RS1_WR_DB", "PCH_RD_DB", "UCC_CLR"],
    ],
}

microcode = generate_microcode(instructions)
write_microcode_to_hex(microcode)

import intelhex

uop = {
    "MCS_CLR": 0,       # Reset microcode step counter
    "PC_INC": 1,        # Increment PC
    "PC_WR_ADDR": 2,    # Write PC to address bus
    "PC_RD_ADDR": 3,    # Load address bus into PC
    "IR0_RD_DB": 4,     # Instruction Register 0 read Data Bus
    "IR1_RD_DB": 5,     # Instruction Register 1 read Data Bus
    "IR2_RD_DB": 6,     # Instruction Register 2 read Data Bus
    "RD_WR_DB": 7,      # Register Destination write Data Bus
    "RD_RD_DB": 8,      # Register Destination read Data Bus
    "RS0_WR_DB": 9,     # Register Source 0 write Data Bus
    "RS1_WR_DB": 10,    # Register Source 1 write Data Bus
    "RS_WR_ADDR": 11,   # Register Sources write Address Bus
    "RS_BUFFER": 12,    # Register Sources buffer (do this before RD_RD_DB)
    "IMM_WR_DB": 13,    # Immediate write Data Bus
    "WR_DB": 14,        # Write Data Bus (write data input to external devices)
    "RD_DB": 15,        # Read Data Bus
    "MEM_WE": 30,       # External memory write enable
    "MEM_OE": 31,       # External memory output enable
}

def generate_microcode(config):
    microcode = {}
    for opcode, steps in config.items():
        for step in range(16):
            address = (opcode << 4) | step  # 4-bit opcode + 4-bit step counter
            if step < len(steps):
                signals = steps[step]
                microcode_word = 0
                print(f"Generating microcode for opcode 0x{opcode:X} at step {step}: {signals}")
                for signal in signals:
                    if signal in uop:
                        microcode_word |= 1 << uop[signal]
                    else:
                        raise ValueError(f"Unknown signal: {signal}")
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
        [ "RS0_WR_DB", "RD_RD_DB", "MCS_CLR"],
        # looks quite nice? rs0 writes data bus, rd reades data bus.
    ],
    0x2: [ # LDI
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["IMM_WR_DB", "RD_RD_DB", "MCS_CLR"],
    ],
    0x3: [ # LOAD
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        # ah.
        ["RS_BUFFER", "RS_WR_ADDR"],
        ["RS_WR_ADDR", "RD_RD_DB", "RD_DB", "MEM_OE", "MCS_CLR"],
],
    0x4: [ # STORE
        ["PC_INC", "PC_WR_ADDR", "IR0_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR1_RD_DB", "RD_DB", "MEM_OE"],
        ["PC_INC", "PC_WR_ADDR", "IR2_RD_DB", "RD_DB", "MEM_OE"],
        ["RS_BUFFER", "RS_WR_ADDR"],
        ["RS_WR_ADDR", "RD_WR_DB", "WR_DB", "MEM_WE", "MCS_CLR"],
    ]
}

microcode = generate_microcode(instructions)
write_microcode_to_hex(microcode)

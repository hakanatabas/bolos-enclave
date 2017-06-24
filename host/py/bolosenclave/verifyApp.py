"""
*******************************************************************************
*   BOLOS Enclave
*   (c) 2017 Ledger
*
*  Licensed under the Apache License, Version 2.0 (the "License");
*  you may not use this file except in compliance with the License.
*  You may obtain a copy of the License at
*
*      http://www.apache.org/licenses/LICENSE-2.0
*
*  Unless required by applicable law or agreed to in writing, software
*  distributed under the License is distributed on an "AS IS" BASIS,
*  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*  See the License for the specific language governing permissions and
*  limitations under the License.
********************************************************************************
"""

import argparse
import struct
import hashlib
from elftools.elf.elffile import ELFFile
from elftools.elf.constants import P_FLAGS
from .ecWrapper import PublicKey

parser = argparse.ArgumentParser()
parser.add_argument("--elf", help="ELF file to hash")
parser.add_argument("--key", help="The public key to verify with (hex encoded)")
parser.add_argument("--signature", help="The signature to verify with (hex encoded)")

args = parser.parse_args()

if args.elf == None:
        raise Exception("No ELF file specified")
if args.key == None:
        raise Exception("Missing public key")
if args.signature == None:
        raise Exception("Missing signature")

f = open(args.elf, "rb")
elffile = ELFFile(f)
m = hashlib.sha256()
for segment in elffile.iter_segments():
        if segment['p_type'] == 'PT_LOAD':
                flags = 0
                if ((segment['p_flags'] & P_FLAGS.PF_W) == 0):
                        flags = flags | 0x01
                m.update(chr(flags))
                m.update(struct.pack(">I", segment['p_vaddr']))
                m.update(struct.pack(">I", segment['p_vaddr'] + segment['p_memsz']))
                m.update(struct.pack(">I", segment['p_filesz']))
                m.update(segment.data())
m.update(struct.pack(">I", elffile.header['e_entry']))
dataToSign = m.digest()

publicKey = PublicKey(bytes(bytearray.fromhex(args.key)), raw=True)
signature = publicKey.ecdsa_deserialize(bytes(bytearray.fromhex(args.signature)))
if not publicKey.ecdsa_verify(bytes(dataToSign), signature, raw=True):
        raise Exception("Signature not verified")

print("Signature verified")

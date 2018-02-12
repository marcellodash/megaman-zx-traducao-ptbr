#!/usr/bin/env python
# -*- coding: windows-1252 -*-

# author: diego.hahn
#

# HARDCODED AO EXTREMO :D 
import struct
import os
import sys

COMPRESSION_FLAG = [0, 0, 0, 0, 0, 0, 0 ]
COMPRESSION_FLAG2 = [0,0,0x80000000,0x80000000,0,0,0x80000000,0,0,0,0,0,0,0,0,0]

PTR2_MARK = [0x80440100,0x80440100,0x80440100,0x80440100,0x80440100,0x80200100,0x80440100,0x80000000,
0x80000000,0x80000000,0x80000000,0x80000000,0x80000000,0x80000000,0x80000000,0x80000000,0x804401c0,
0x804401c0,0x804401c0,0x804401c0,0x804401c0,0x804401c0,0x804401c0,0x804401c0,0x804401c0,0x804401c0,
0x804401c0,0x804401c0,0x804401c0,0x804401c0,0x804401c0,0x804401c0,]
P = [ 0, 0, 0, 0, 0, 0x0f, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def Unpack(src, dst):
    print ">> Unpacking sub.bin"
    
    ptr_table_1_path = os.path.join( dst, "ptr_table_1" )
    if not os.path.isdir(ptr_table_1_path):
        os.makedirs(ptr_table_1_path)    
    
    with open( src , "rb" ) as fd:
            
        fd.seek( 0x04 )       
        for i in range(5):
            addr, next = struct.unpack("<LL", fd.read(8))
            addr &= 0x7fffffff
            next &= 0x7fffffff 
            size = next - addr
            link = fd.tell() - 4
            
            fd.seek( addr )          
            with open( os.path.join(ptr_table_1_path , "%03d.bin" % i) , "wb" ) as out:
                out.write( fd.read( size ) )                
            fd.seek( link )
    
    # Este arquivo importa
    with open( os.path.join( ptr_table_1_path , "000.bin" ), "rb" ) as fd:
    
        ptr_table_2_path = os.path.join( ptr_table_1_path, "000" )
        if not os.path.isdir(ptr_table_2_path):
            os.makedirs(ptr_table_2_path)
    
        for i in range(32):
            addr = fd.tell() + struct.unpack("<L" , fd.read(4))[0]
            size = struct.unpack("<L" , fd.read(4))[0] & 0x7fffffff
            dummy = struct.unpack("<L", fd.read(4))[0]
            addr_palette = fd.tell() + struct.unpack("<L" , fd.read(4))[0]
            size_palette = struct.unpack("<L" , fd.read(4))[0] & 0xFF
            print hex(addr), hex(size), hex(dummy), hex(addr_palette), hex(size_palette)
            
            link = fd.tell()
            
            with open( os.path.join( ptr_table_2_path , "%03d.bin" % i ) , "wb" ) as od:
                fd.seek( addr )
                #print hex(link)
               # print size
                od.write( fd.read( size ) )
            
            with open( os.path.join( ptr_table_2_path , "%03d_palette.bin" % i ) , "wb" ) as od:
                fd.seek( addr_palette )
                od.write( fd.read( size_palette ) )            
            fd.seek( link )
            
# 0x00000078 -> Ponteiro pro arquivo + f.tell()
# 0x00007320 -> Tamanho do arquivo
# 0x80460100 -> ??
# 0x0000738C -> Ponteiro pra paleta de cores + f.tell()
# 0x00080000 -> ??          

def Pack(src, dst):
    print ">> Packing sub.bin"
    
    ptr_table_1_path = os.path.join( src, "ptr_table_1" )
    if not os.path.isdir(ptr_table_1_path):
        os.makedirs(ptr_table_1_path)  

    ptr_table_2_path = os.path.join( ptr_table_1_path, "000" )
    if not os.path.isdir(ptr_table_2_path):
        os.makedirs(ptr_table_2_path)

    files = os.listdir(ptr_table_2_path)
    splitted_files = [ f for f in files if "palette" not in f ]
    splitted_pallete = [ f for f in files if "palette" in f ]        
    
    # Este arquivo importa
    with open( os.path.join( ptr_table_1_path , "000.bin" ), "wb" ) as fd:
        # 32 entradas
        # 5 campos
        # 4 bytes
        fd.seek( 32 * 5 * 4)
        
        ptr_table_2_table = []
        
        for i, f in enumerate(splitted_files):
            addr = fd.tell()
            print os.path.join(ptr_table_2_path, f)
            input = open( os.path.join(ptr_table_2_path, f), "rb" )
            
            if i >= 16:
                buff = input.read(3584)
                fd.write( buff )
                #size = 0x49c00e00 # Ponto de VRAM das carinhas dos personagens
                size = 0x4ec00e00 # Ponto de VRAM das carinhas dos personagens
            else:
                buff = input.read()
                fd.write( buff )
                size = len(buff) | COMPRESSION_FLAG2[i]
            
            input.close()
            if ( fd.tell() % 4 != 0 ):
                fd.write( "\x00" * (4 - (fd.tell() % 4)) )
            
            paddr = fd.tell()            
            if ("%03d_palette.bin" % i) in splitted_pallete:
                input = open( os.path.join(ptr_table_2_path, ("%03d_palette.bin" % i)), "rb" )
                buff = input.read()
                fd.write( buff )
                input.close()
                
                psize = len(buff)
            else:
                psize = 0
            
            ptr_table_2_table.append( (addr, size, PTR2_MARK[i], paddr, psize) )   
            
        fd.seek(0x0)           
        for i, p in enumerate(ptr_table_2_table):
            fd.write( struct.pack( "<L", p[0] - fd.tell() ))
            fd.write( struct.pack( "<L", p[1] ))
            fd.write( struct.pack( "<L", p[2] ))
            fd.write( struct.pack( "<L", p[3] - fd.tell() ))
            fd.write( struct.pack( "<L", p[4] | 0x00080000 | P[i] << 24 ))        
    
    with open( dst, "wb" ) as fd:    
        fd.write( struct.pack("<L", 0x000005) )
        fd.seek( 0x1c )
        
        ptr_table_1_table = []
        for i, f in enumerate(range(5)): 
            addr = fd.tell()
        
            input = open( os.path.join(ptr_table_1_path, "%03d.bin" % f), "rb" )
            fd.write( input.read() )
            input.close()
            
            if ( fd.tell() % 4 != 0 ):
                fd.write( "\x00" * (4 - (fd.tell() % 4)) )            
            
            ptr_table_1_table.append(addr)
        ptr_table_1_table.append(fd.tell())        
        
        fd.seek( 0x04 )
        for i, p in enumerate(ptr_table_1_table):
            fd.write( struct.pack( "<L", p | COMPRESSION_FLAG[i] ))    
    
if __name__ == "__main__":

    import argparse
    
    os.chdir( sys.path[0] )
    #os.system( 'cls' )

    parser = argparse.ArgumentParser()
    parser.add_argument( '-m', dest = "mode", type = str, required = True )
    parser.add_argument( '-s', dest = "src", type = str, nargs = "?", required = True )
    parser.add_argument( '-d', dest = "dst", type = str, nargs = "?", required = True )
    
    args = parser.parse_args()            

    if args.mode == "u":
        Unpack( args.src , args.dst )
    elif args.mode == "p": 
        Pack( args.src , args.dst  )
    else:
        sys.exit(1)               
        
    

            
    
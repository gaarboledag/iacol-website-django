#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para optimizar imágenes y crear versiones responsivas
"""
from PIL import Image
import os
import sys

# Configurar la salida para UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def optimize_main_image():
    """Optimiza la imagen principal main.webp"""
    print("Optimizando main.webp...")
    
    input_path = 'static/img/main.webp'
    
    if not os.path.exists(input_path):
        print(f"[X] No se encontro {input_path}")
        return
    
    try:
        img = Image.open(input_path)
        print(f"[OK] Imagen original: {img.size[0]}x{img.size[1]}px")
        
        # Crear versiones optimizadas
        sizes = [
            (400, 218, 'main-400.webp', 'moviles'),
            (668, 364, 'main-668.webp', 'tablets/PC'),
            (1024, 559, 'main-1024.webp', 'pantallas grandes')
        ]
        
        for width, height, filename, description in sizes:
            output_path = f'static/img/{filename}'
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output_path, 'WEBP', quality=85, method=6)
            file_size = os.path.getsize(output_path) / 1024
            print(f"[OK] Creado {filename} ({width}x{height}px) - {file_size:.1f} KB - para {description}")
        
        print("[EXITO] main.webp optimizado correctamente\n")
        
    except Exception as e:
        print(f"[ERROR] Error al optimizar main.webp: {e}\n")

def optimize_logo():
    """Optimiza el logo iacol_logo_horizontal.png"""
    print("Optimizando iacol_logo_horizontal.png...")
    
    input_path = 'static/img/iacol_logo_horizontal.png'
    
    if not os.path.exists(input_path):
        print(f"[X] No se encontro {input_path}")
        return
    
    try:
        img = Image.open(input_path)
        print(f"[OK] Logo original: {img.size[0]}x{img.size[1]}px")
        
        # Crear versiones optimizadas
        sizes = [
            (130, 28, 'iacol_logo_horizontal-130.png', 'PC'),
            (227, 49, 'iacol_logo_horizontal-227.png', 'moviles'),
            (260, 56, 'iacol_logo_horizontal-260.png', 'tablets'),
            (932, 201, 'iacol_logo_horizontal-932.png', 'pantallas retina')
        ]
        
        for width, height, filename, description in sizes:
            output_path = f'static/img/{filename}'
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            resized.save(output_path, 'PNG', optimize=True)
            file_size = os.path.getsize(output_path) / 1024
            print(f"[OK] Creado {filename} ({width}x{height}px) - {file_size:.1f} KB - para {description}")
        
        print("[EXITO] Logo optimizado correctamente\n")
        
    except Exception as e:
        print(f"[ERROR] Error al optimizar logo: {e}\n")

if __name__ == '__main__':
    print("=" * 60)
    print("OPTIMIZACION DE IMAGENES PARA IACOL WEBSITE")
    print("=" * 60)
    print()
    
    optimize_main_image()
    optimize_logo()
    
    print("=" * 60)
    print("[EXITO] PROCESO COMPLETADO")
    print("=" * 60)
    print("\nProximos pasos:")
    print("1. Actualizar templates/home.html con srcset para main.webp")
    print("2. Actualizar templates/base.html con srcset para el logo")

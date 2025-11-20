# API de Creación de Blog Posts - N8N Integration

## 📋 Descripción General

Esta API permite crear entradas del blog desde herramientas externas como N8N de manera segura y estructurada.

## 🔐 Autenticación

### API Key Authentication
- **Header**: `X-API-Key: your-api-key-here`
- **Alternativo**: `Authorization: Bearer your-api-key-here`

### Gestión de API Keys
1. Ve al admin: `/admin/blog/apikey/`
2. Crea una nueva clave API
3. Asigna a un usuario existente
4. Activa la clave

## 🚀 Endpoint

### Crear Blog Post
```
POST /blog/api/create-post/
```

### Headers Requeridos
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

## 📝 Payload de Ejemplo

```json
{
  "title": "Cómo Automatizar tu Taller con IA",
  "category": "guias",
  "excerpt": "Guía completa para implementar IA en talleres automotrices",
  "is_published": false,
  "meta_description": "Descubre cómo la IA puede revolucionar tu taller automotriz",

  "problem_section": "Los talleres tradicionales pierden tiempo en tareas repetitivas...",
  "why_automate_section": "La automatización libera tiempo para tareas de mayor valor...",
  "sales_angle_section": "Nuestra solución combina IA avanzada con experiencia automotriz...",
  "how_it_works_section": "El sistema utiliza algoritmos de machine learning...",
  "benefits_section": "Aumenta la productividad en un 300%, reduce errores...",
  "hypothetical_case_section": "Imagina un taller que procesa 50 vehículos diarios...",
  "final_cta_section": "Comienza tu transformación digital hoy mismo",

  "hero_image_url": "https://example.com/hero-image.jpg",
  "problem_image_url": "https://example.com/problem-diagram.jpg"
}
```

## 🎯 Campos Obligatorios

- `title` (string, 5-200 chars)
- `category` (choice: 'guias', 'casos', 'faq')

## 🎯 Campos Opcionales

### Texto
- `excerpt` (string, máx 300 chars)
- `meta_description` (string, máx 160 chars)
- `is_published` (boolean, default: false)

### Contenido Estructurado
- `problem_section`
- `why_automate_section`
- `sales_angle_section`
- `how_it_works_section`
- `benefits_section`
- `hypothetical_case_section`
- `final_cta_section`

### Imágenes (URLs externas)
- `hero_image_url`: URL externa de la imagen principal
- `problem_image_url`: URL externa de la imagen del problema

**Nota:** También puedes subir archivos directamente desde el admin, pero las URLs tienen prioridad para display.

## 📤 Respuesta Exitosa

```json
{
  "success": true,
  "message": "Blog post created successfully",
  "data": {
    "id": 123,
    "title": "Cómo Automatizar tu Taller con IA",
    "slug": "como-automatizar-tu-taller-con-ia",
    "url": "https://tu-dominio.com/blog/como-automatizar-tu-taller-con-ia/",
    "is_published": false,
    "category": "guias",
    "created_at": "2025-11-16T16:41:00Z"
  }
}
```

## ❌ Respuesta de Error

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "title": ["Este campo es obligatorio"],
    "category": ["Categoría debe ser una de: guias, casos, faq"]
  }
}
```

## 🛡️ Seguridad y Límites

### Rate Limiting
- **10 requests por minuto** por API key
- Aplicable solo al endpoint de creación

### Validaciones
- Autenticación requerida
- Validación de tipos de datos
- Sanitización de contenido HTML
- Validación de URLs de imágenes
- Límites de tamaño de archivos

### Logging
- Todas las requests se loggean
- Incluye usuario, timestamp y resultado
- Útil para debugging y auditoría

## 🔧 Configuración en N8N

### Nodo HTTP Request
1. **Method**: POST
2. **URL**: `https://tu-dominio.com/blog/api/create-post/`
3. **Headers**:
   ```
   Content-Type: application/json
   X-API-Key: your-api-key-here
   ```
4. **Body**: JSON con los datos del post

### Manejo de Errores
- Verifica `success: true` en la respuesta
- Si falla, revisa el campo `errors`
- Implementa reintentos con backoff

## 📊 Testing del Endpoint

### Endpoint de Status
```
GET /blog/api/status/
```
Verifica conectividad y autenticación.

### Ejemplo de Test con curl
```bash
curl -X POST https://tu-dominio.com/blog/api/create-post/ \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "title": "Test Post",
    "category": "guias",
    "excerpt": "Test excerpt"
  }'
```

## 🚨 Consideraciones de Producción

1. **HTTPS Obligatorio**: Solo permite conexiones seguras
2. **Validación de Imágenes**: Verifica tamaños y tipos
3. **Monitoreo**: Implementa alertas para rate limits
4. **Backup**: Las imágenes se almacenan en el servidor
5. **Cache**: Considera cache para imágenes descargadas

## 🆘 Troubleshooting

### Error: "Invalid API key"
- Verifica que la API key existe y está activa
- Confirma el header `X-API-Key`

### Error: "Rate limit exceeded"
- Espera 1 minuto antes de reintentar
- Reduce la frecuencia de requests

### Error: "Image download failed"
- Verifica que la URL sea accesible
- Confirma que la imagen no exceda límites de tamaño

### Error: "Validation failed"
- Revisa los campos requeridos
- Verifica formatos de datos

## 📞 Soporte

Para problemas con la API:
1. Revisa los logs del servidor
2. Verifica la configuración de N8N
3. Contacta al administrador del sistema
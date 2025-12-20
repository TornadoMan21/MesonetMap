# Memory optimization settings for Render.com deployment

# Reduce memory usage by limiting data processing
MAX_STATIONS_PER_SOURCE = {
    'maryland': 5,
    'virginia': 15, 
    'newyork': 14,
    'pennsylvania': 20,
    'asos': 15
}

# Grid resolution for contour generation (lower = less memory)
CONTOUR_GRID_SIZE = 40  # Reduced from 80

# Image quality settings (lower DPI = less memory)
MAP_DPI = 200  # Reduced from 300
MAP_FIGURE_SIZE = (8, 6)  # Reduced from (12, 8)

# Memory cleanup intervals
ENABLE_GARBAGE_COLLECTION = True
CLEANUP_AFTER_EACH_SOURCE = True

# Render.com specific optimizations
MAX_WORKER_MEMORY_LIMIT = "512MB"
ENABLE_MEMORY_PROFILING = False
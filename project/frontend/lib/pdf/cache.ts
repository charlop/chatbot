/**
 * PDF Text Location Cache
 *
 * In-memory cache for text search results to avoid re-searching
 * the same text on every component re-render.
 */

interface TextLocation {
  text: string;
  page: number;
  bbox: { x: number; y: number; width: number; height: number };
}

/**
 * Simple LRU cache for text locations
 */
class TextLocationCache {
  private cache: Map<string, TextLocation>;
  private maxSize: number;

  constructor(maxSize: number = 100) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  /**
   * Generate cache key from contract, page, and text
   */
  private getCacheKey(contractId: string, page: number, text: string): string {
    return `${contractId}:${page}:${text}`;
  }

  /**
   * Get cached text location
   */
  get(contractId: string, page: number, text: string): TextLocation | null {
    const key = this.getCacheKey(contractId, page, text);
    const cached = this.cache.get(key);

    if (cached) {
      // Move to end (LRU)
      this.cache.delete(key);
      this.cache.set(key, cached);
      return cached;
    }

    return null;
  }

  /**
   * Set cached text location
   */
  set(contractId: string, page: number, text: string, location: TextLocation): void {
    const key = this.getCacheKey(contractId, page, text);

    // Remove oldest if at capacity
    if (this.cache.size >= this.maxSize) {
      const firstKey = this.cache.keys().next().value;
      if (firstKey) {
        this.cache.delete(firstKey);
      }
    }

    this.cache.set(key, location);
  }

  /**
   * Clear cache for a specific contract
   */
  clearContract(contractId: string): void {
    const keysToDelete: string[] = [];

    for (const key of this.cache.keys()) {
      if (key.startsWith(`${contractId}:`)) {
        keysToDelete.push(key);
      }
    }

    keysToDelete.forEach(key => this.cache.delete(key));
  }

  /**
   * Clear entire cache
   */
  clear(): void {
    this.cache.clear();
  }

  /**
   * Get cache size
   */
  size(): number {
    return this.cache.size;
  }
}

// Global singleton cache instance
export const textLocationCache = new TextLocationCache(100);

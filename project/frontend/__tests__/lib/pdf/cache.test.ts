import { describe, it, expect, beforeEach } from 'vitest';
import { textLocationCache } from '@/lib/pdf/cache';

describe('TextLocationCache', () => {
  beforeEach(() => {
    textLocationCache.clear();
  });

  it('should cache and retrieve text locations', () => {
    const location = {
      text: 'GAP Premium: $500',
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
    };

    textLocationCache.set('contract-001', 1, 'GAP Premium: $500', location);

    const cached = textLocationCache.get('contract-001', 1, 'GAP Premium: $500');
    expect(cached).toEqual(location);
  });

  it('should return null for non-cached items', () => {
    const cached = textLocationCache.get('contract-001', 1, 'Non-existent text');
    expect(cached).toBeNull();
  });

  it('should handle multiple contracts', () => {
    const location1 = {
      text: 'Text 1',
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
    };

    const location2 = {
      text: 'Text 2',
      page: 1,
      bbox: { x: 150, y: 150, width: 180, height: 18 },
    };

    textLocationCache.set('contract-001', 1, 'Text 1', location1);
    textLocationCache.set('contract-002', 1, 'Text 2', location2);

    expect(textLocationCache.get('contract-001', 1, 'Text 1')).toEqual(location1);
    expect(textLocationCache.get('contract-002', 1, 'Text 2')).toEqual(location2);
  });

  it('should clear cache for specific contract', () => {
    const location1 = {
      text: 'Text 1',
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
    };

    const location2 = {
      text: 'Text 2',
      page: 1,
      bbox: { x: 150, y: 150, width: 180, height: 18 },
    };

    textLocationCache.set('contract-001', 1, 'Text 1', location1);
    textLocationCache.set('contract-002', 1, 'Text 2', location2);

    textLocationCache.clearContract('contract-001');

    expect(textLocationCache.get('contract-001', 1, 'Text 1')).toBeNull();
    expect(textLocationCache.get('contract-002', 1, 'Text 2')).toEqual(location2);
  });

  it('should clear entire cache', () => {
    const location = {
      text: 'Test text',
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
    };

    textLocationCache.set('contract-001', 1, 'Test text', location);
    expect(textLocationCache.size()).toBe(1);

    textLocationCache.clear();
    expect(textLocationCache.size()).toBe(0);
    expect(textLocationCache.get('contract-001', 1, 'Test text')).toBeNull();
  });

  it('should implement LRU eviction when at capacity', () => {
    // Create cache with small max size for testing
    // Note: We're using the global cache, so we'll just fill it
    const maxSize = 100; // Default max size

    // Fill cache to capacity
    for (let i = 0; i < maxSize; i++) {
      textLocationCache.set(
        'contract-001',
        i,
        `text-${i}`,
        {
          text: `text-${i}`,
          page: i,
          bbox: { x: 100, y: 100, width: 200, height: 20 },
        }
      );
    }

    expect(textLocationCache.size()).toBe(maxSize);

    // Add one more - should evict the oldest
    textLocationCache.set(
      'contract-001',
      maxSize,
      `text-${maxSize}`,
      {
        text: `text-${maxSize}`,
        page: maxSize,
        bbox: { x: 100, y: 100, width: 200, height: 20 },
      }
    );

    expect(textLocationCache.size()).toBe(maxSize);

    // First item should be evicted
    expect(textLocationCache.get('contract-001', 0, 'text-0')).toBeNull();

    // Last item should be present
    expect(textLocationCache.get('contract-001', maxSize, `text-${maxSize}`)).toBeTruthy();
  });

  it('should handle same text on different pages', () => {
    const location1 = {
      text: 'Same text',
      page: 1,
      bbox: { x: 100, y: 100, width: 200, height: 20 },
    };

    const location2 = {
      text: 'Same text',
      page: 2,
      bbox: { x: 150, y: 150, width: 180, height: 18 },
    };

    textLocationCache.set('contract-001', 1, 'Same text', location1);
    textLocationCache.set('contract-001', 2, 'Same text', location2);

    expect(textLocationCache.get('contract-001', 1, 'Same text')).toEqual(location1);
    expect(textLocationCache.get('contract-001', 2, 'Same text')).toEqual(location2);
  });
});

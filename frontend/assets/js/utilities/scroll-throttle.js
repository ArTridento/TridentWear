/**
 * Scroll Throttle Utility
 * Combines multiple scroll listeners into a single throttled listener for better performance
 * Prevents jank on mobile by reducing calculation frequency
 *
 * Usage:
 * const scrollManager = new ScrollThrottleManager();
 * scrollManager.onScroll((scrollY) => { myParallaxLogic(scrollY); });
 * scrollManager.start();
 */

export class ScrollThrottleManager {
  constructor(throttleMs = 16) {
    // 16ms ≈ 60fps, optimal for smooth 60fps scrolling
    this.throttleMs = throttleMs;
    this.scrollY = 0;
    this.lastUpdateTime = 0;
    this.listeners = [];
    this.isActive = false;
    this.onScrollFn = null;

    // Bind to preserve 'this' context
    this.handleScroll = this.handleScroll.bind(this);
  }

  /**
   * Add a callback to be called on throttled scroll
   * @param {Function} callback - Function that receives scrollY value
   */
  onScroll(callback) {
    this.listeners.push(callback);
  }

  /**
   * Handle scroll event with throttling
   * @private
   */
  handleScroll() {
    const now = performance.now();
    this.scrollY = window.scrollY;

    // Only update if throttle time has elapsed
    if (now - this.lastUpdateTime >= this.throttleMs) {
      this.lastUpdateTime = now;

      // Call all registered listeners
      this.listeners.forEach(listener => {
        try {
          listener(this.scrollY);
        } catch (e) {
          console.error('Error in scroll listener:', e);
        }
      });
    }
  }

  /**
   * Start listening to scroll events
   */
  start() {
    if (this.isActive) return;
    this.isActive = true;
    window.addEventListener('scroll', this.handleScroll, { passive: true });
  }

  /**
   * Stop listening to scroll events
   */
  stop() {
    if (!this.isActive) return;
    this.isActive = false;
    window.removeEventListener('scroll', this.handleScroll);
  }

  /**
   * Get current scroll Y position
   * @returns {number} Current scroll Y value
   */
  getScrollY() {
    return this.scrollY;
  }

  /**
   * Destroy and cleanup
   */
  destroy() {
    this.stop();
    this.listeners = [];
  }
}

/**
 * Helper to create a single global throttle manager
 * Avoids multiple scroll listeners
 */
export function createGlobalScrollManager() {
  if (window.__scrollManager) {
    return window.__scrollManager;
  }

  const manager = new ScrollThrottleManager(16);
  manager.start();
  window.__scrollManager = manager;

  return manager;
}

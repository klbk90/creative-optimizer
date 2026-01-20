/**
 * Creative Optimizer Tracking Script
 *
 * Simple 1-line integration for tracking conversions
 * Usage: Add this script to your website <head>
 */

(function() {
  'use strict';

  // Configuration
  const API_URL = 'https://creative-optimizer.vercel.app/api/v1';

  // Get UTM parameters from URL
  function getUTMParams() {
    const params = new URLSearchParams(window.location.search);
    return {
      utm_id: params.get('utm_id'),
      utm_source: params.get('utm_source'),
      utm_campaign: params.get('utm_campaign'),
      utm_content: params.get('utm_content')
    };
  }

  // Store UTM params in sessionStorage for later use
  function storeUTMParams() {
    const utmParams = getUTMParams();
    if (utmParams.utm_id) {
      sessionStorage.setItem('creative_optimizer_utm', JSON.stringify(utmParams));
    }
  }

  // Track conversion event
  function trackConversion(eventName, data = {}) {
    const storedUTM = sessionStorage.getItem('creative_optimizer_utm');
    if (!storedUTM) {
      console.log('[Creative Optimizer] No UTM params found, skipping tracking');
      return;
    }

    const utmParams = JSON.parse(storedUTM);

    const payload = {
      creative_id: utmParams.utm_id,
      event: eventName,
      revenue: data.revenue || 0,
      customer_id: data.customer_id || null,
      metadata: {
        ...data,
        url: window.location.href,
        timestamp: new Date().toISOString()
      }
    };

    // Send to API
    fetch(`${API_URL}/conversion`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(result => {
      console.log('[Creative Optimizer] Conversion tracked:', result);
    })
    .catch(error => {
      console.error('[Creative Optimizer] Tracking failed:', error);
    });
  }

  // Initialize on page load
  storeUTMParams();

  // Expose global tracking function
  window.creativeOptimizer = {
    track: trackConversion,

    // Convenience methods
    trackPurchase: function(revenue, orderId) {
      trackConversion('purchase', {
        revenue: revenue,
        order_id: orderId
      });
    },

    trackSignup: function(email) {
      trackConversion('signup', {
        customer_id: email
      });
    },

    trackTrial: function(email) {
      trackConversion('trial_start', {
        customer_id: email
      });
    }
  };

  console.log('[Creative Optimizer] Tracking initialized');
})();

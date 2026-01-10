import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

// Pain point messaging
const PAIN_MESSAGES = {
  no_time: {
    headline: "Learn Python in Just 15 Minutes a Day",
    subheadline: "Busy schedule? No problem. Master coding without sacrificing your free time.",
    benefit: "⏰ Bite-sized lessons that fit your schedule"
  },
  too_expensive: {
    headline: "Professional Python Course for Just $49",
    subheadline: "Why pay $500+ when you can get the same results for 10x less?",
    benefit: "💰 Same quality, fraction of the price"
  },
  fear_failure: {
    headline: "95% of Our Students Get Their First Dev Job",
    subheadline: "Stop worrying about failure. Our proven method works even for complete beginners.",
    benefit: "✅ Step-by-step guidance from zero to hired"
  },
  no_progress: {
    headline: "See Real Results in Your First Week",
    subheadline: "Tired of courses where you don't see progress? Build your first app in 7 days.",
    benefit: "🚀 Ship real projects, not just watch videos"
  },
  need_career_switch: {
    headline: "From Teacher to Developer in 6 Months",
    subheadline: "Switching careers? Join 1,200+ professionals who made the leap with us.",
    benefit: "💼 Career-focused curriculum with job placement support"
  },
  imposter_syndrome: {
    headline: "No Coding Experience? Start Here.",
    subheadline: "Everyone feels like an imposter at first. Our beginner-friendly approach makes it easy.",
    benefit: "🎯 Built for absolute beginners"
  },
  info_overload: {
    headline: "Only What You Need to Get Hired",
    subheadline: "Cut through the noise. Learn exactly what employers want, nothing more.",
    benefit: "🎓 Curated curriculum, zero fluff"
  }
};

const COURSES = {
  python: {
    name: "Master Python in 30 Days",
    price: 49.00,
    oldPrice: 98.00,
    instructor: "Alex Rodriguez",
    students: 12453,
    rating: 4.8,
  },
  design: {
    name: "UI/UX Design Bootcamp",
    price: 59.00,
    oldPrice: 118.00,
    instructor: "Sarah Chen",
    students: 8234,
    rating: 4.9,
  },
  english: {
    name: "Business English Mastery",
    price: 39.00,
    oldPrice: 78.00,
    instructor: "Michael Johnson",
    students: 15678,
    rating: 4.7,
  }
};

export default function EdTechLanding() {
  const [searchParams] = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({ name: '', email: '' });

  // Get params from URL
  const painPoint = searchParams.get('pain_point') || 'no_time';
  const courseType = searchParams.get('course') || 'python';
  const utmId = searchParams.get('utm_id');

  const messaging = PAIN_MESSAGES[painPoint] || PAIN_MESSAGES.no_time;
  const course = COURSES[courseType] || COURSES.python;

  useEffect(() => {
    // Initialize RudderStack
    initRudderStack();
  }, []);

  const initRudderStack = () => {
    // Check if RudderStack is loaded
    if (typeof window.rudderanalytics === 'undefined') {
      console.warn('RudderStack not loaded');
      return;
    }

    // Get stored UTM or from URL
    const storedUtm = getStoredUtm();
    const finalUtm = utmId ? { utm_id: utmId } : storedUtm;

    // Save UTM if from URL
    if (utmId) {
      saveUtmToStorage({ utm_id: utmId, utm_source: searchParams.get('utm_source') });
    }

    // Send Page Viewed event
    window.rudderanalytics.page({
      properties: {
        ...finalUtm,
        page_url: window.location.href,
        course_name: course.name,
        pain_point: painPoint,
      }
    });

    console.log('✅ RudderStack Page Viewed sent');
  };

  const getStoredUtm = () => {
    const stored = localStorage.getItem('utm_params');
    if (!stored) return null;

    const data = JSON.parse(stored);
    if (Date.now() > data.expiry) {
      localStorage.removeItem('utm_params');
      return null;
    }

    return data;
  };

  const saveUtmToStorage = (utmParams) => {
    const expiry = Date.now() + (30 * 24 * 60 * 60 * 1000); // 30 days
    localStorage.setItem('utm_params', JSON.stringify({
      ...utmParams,
      expiry
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const anonymousId = window.rudderanalytics?.getAnonymousId();
      const storedUtm = getStoredUtm();

      // Send checkout request
      const response = await fetch('/api/v1/edtech/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...formData,
          utm_id: storedUtm?.utm_id,
          anonymous_id: anonymousId,
        })
      });

      const data = await response.json();

      if (response.ok) {
        // Identify user
        window.rudderanalytics?.identify(data.user_id, {
          email: formData.email,
          name: formData.name,
        });

        // Send Order Completed event
        window.rudderanalytics?.track('Order Completed', {
          order_id: data.order_id,
          total: course.price,
          currency: 'USD',
          product_name: course.name,
          product_id: `${courseType}_course_001`,
          utm_id: storedUtm?.utm_id,
        });

        console.log('✅ Order Completed event sent');

        // Redirect to success page
        window.location.href = `/api/v1/edtech/success?order_id=${data.order_id}`;
      } else {
        alert('Error: ' + (data.detail || 'Payment failed'));
      }
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-purple-700 to-indigo-800">
      <div className="container mx-auto px-4 py-12">
        {/* Hero Section */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-16 mb-12 text-center">
          <h1 className="text-4xl md:text-6xl font-extrabold text-purple-600 mb-6 leading-tight">
            {messaging.headline}
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8">
            {messaging.subheadline}
          </p>

          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <div className="inline-flex items-center gap-2 bg-purple-50 px-6 py-3 rounded-xl font-semibold">
              <span className="text-yellow-500 text-xl">⭐⭐⭐⭐⭐</span>
              <span>{course.rating} ({course.students.toLocaleString()} students)</span>
            </div>
            <div className="inline-flex items-center gap-2 bg-purple-50 px-6 py-3 rounded-xl font-semibold">
              <span>👨‍🏫</span>
              <span>Taught by {course.instructor}</span>
            </div>
          </div>
        </div>

        {/* Benefits Section */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h3 className="text-2xl font-bold text-purple-600 mb-4">
              {messaging.benefit}
            </h3>
            <p className="text-gray-600">
              Our proven methodology has helped thousands of students achieve their coding goals, even with busy schedules.
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h3 className="text-2xl font-bold text-purple-600 mb-4">
              🎯 Real Projects, Real Skills
            </h3>
            <p className="text-gray-600">
              Build 10+ portfolio projects you can show to employers. No more tutorial hell.
            </p>
          </div>

          <div className="bg-white rounded-2xl shadow-lg p-8">
            <h3 className="text-2xl font-bold text-purple-600 mb-4">
              💬 Lifetime Community Access
            </h3>
            <p className="text-gray-600">
              Join our private community of {course.students.toLocaleString()}+ students. Get help anytime, network, and find job opportunities.
            </p>
          </div>
        </div>

        {/* Urgency Banner */}
        <div className="bg-red-500 text-white text-center py-5 rounded-xl font-bold text-lg mb-12">
          🔥 Limited Time Offer: 50% OFF expires in 24 hours!
        </div>

        {/* Pricing & Checkout */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-16 text-center">
          <h2 className="text-3xl font-bold mb-6">Get Instant Access Today</h2>

          <div className="mb-8">
            <div className="text-gray-400 text-3xl line-through mb-2">
              ${course.oldPrice.toFixed(0)}
            </div>
            <div className="text-6xl font-extrabold text-purple-600 mb-4">
              ${course.price.toFixed(0)}
            </div>
            <p className="text-gray-600">One-time payment. Lifetime access. No subscriptions.</p>
          </div>

          {/* Checkout Form */}
          <form onSubmit={handleSubmit} className="max-w-md mx-auto">
            <div className="mb-4">
              <label className="block text-left font-semibold mb-2 text-gray-700">
                Full Name
              </label>
              <input
                type="text"
                required
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none text-lg"
              />
            </div>

            <div className="mb-6">
              <label className="block text-left font-semibold mb-2 text-gray-700">
                Email Address
              </label>
              <input
                type="email"
                required
                placeholder="john@example.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:outline-none text-lg"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-4 px-8 rounded-full text-xl font-bold shadow-lg hover:shadow-xl transform hover:-translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : `Enroll Now - $${course.price.toFixed(0)}`}
            </button>
          </form>

          <p className="mt-6 text-gray-500 text-sm">
            🔒 Secure checkout. 30-day money-back guarantee.
          </p>
        </div>
      </div>
    </div>
  );
}

import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center py-20 bg-gradient-to-r from-primary-600 to-primary-800 text-white rounded-2xl shadow-2xl">
        <h1 className="text-5xl font-bold mb-6">
          Government Contracts Made Simple
        </h1>
        <p className="text-xl mb-8 max-w-2xl mx-auto">
          AI-powered platform that discovers, classifies, and delivers government procurement opportunities from all 50 states.
        </p>
        <div className="flex justify-center space-x-4">
          <Link
            to="/register"
            className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-primary-50 transition text-lg"
          >
            Start Free Trial
          </Link>
          <Link
            to="/rfps"
            className="bg-primary-700 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-800 transition text-lg border-2 border-white"
          >
            Browse Opportunities
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section>
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-800">
          Why ContractLink AI?
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon="🤖"
            title="AI-Powered Classification"
            description="Our GPT-4 engine automatically categorizes RFPs by industry, saving you hours of manual review."
          />
          <FeatureCard
            icon="🗺️"
            title="50 State Coverage"
            description="Automated scrapers monitor state and city portals 24/7, ensuring you never miss an opportunity."
          />
          <FeatureCard
            icon="🔔"
            title="Smart Notifications"
            description="Get daily digests of relevant RFPs matching your preferences and business profile."
          />
          <FeatureCard
            icon="🏙️"
            title="City Portal Discovery"
            description="AI discovers and monitors city-level procurement portals automatically."
          />
          <FeatureCard
            icon="📊"
            title="Real-Time Dashboard"
            description="Track your bookmarked opportunities, vendor registrations, and application status."
          />
          <FeatureCard
            icon="⚡"
            title="Instant Alerts"
            description="Get notified immediately when high-value contracts matching your criteria are posted."
          />
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-primary-50 rounded-2xl p-12">
        <div className="grid md:grid-cols-4 gap-8 text-center">
          <StatCard number="50" label="States Covered" />
          <StatCard number="500+" label="City Portals" />
          <StatCard number="10K+" label="Active RFPs" />
          <StatCard number="95%" label="Classification Accuracy" />
        </div>
      </section>

      {/* CTA Section */}
      <section className="text-center py-16 bg-gradient-to-r from-gray-800 to-gray-900 text-white rounded-2xl">
        <h2 className="text-4xl font-bold mb-4">
          Ready to Win More Contracts?
        </h2>
        <p className="text-xl mb-8">
          Join contractors winning with AI-powered procurement intelligence.
        </p>
        <Link
          to="/register"
          className="bg-primary-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-600 transition text-lg"
        >
          Get Started Today
        </Link>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-bold mb-2 text-gray-800">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function StatCard({ number, label }) {
  return (
    <div>
      <div className="text-4xl font-bold text-primary-600 mb-2">{number}</div>
      <div className="text-gray-700 font-medium">{label}</div>
    </div>
  );
}

export default function StatesPage() {
  const states = [
    { code: 'CA', name: 'California', rfps: 245 },
    { code: 'TX', name: 'Texas', rfps: 198 },
    { code: 'NY', name: 'New York', rfps: 156 },
    { code: 'FL', name: 'Florida', rfps: 134 },
    { code: 'VA', name: 'Virginia', rfps: 89 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-800">State Procurement Portals</h1>
      
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {states.map((state) => (
          <div key={state.code} className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="text-xl font-bold text-gray-800 mb-2">{state.name}</h3>
            <p className="text-gray-600 mb-4">{state.rfps} active RFPs</p>
            <a
              href={`/rfps?source_state=${state.code}`}
              className="text-primary-600 font-medium hover:underline"
            >
              View Opportunities →
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}

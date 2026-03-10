"use client"

import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { api } from '@/lib/api'
import { Navbar } from '@/components/Navbar'
import { Footer } from '@/components/Footer'

export default function UpgradePage() {
  const searchParams = useSearchParams()
  const { user, loading: authLoading } = useAuth()
  const [loading, setLoading] = useState(false)
  const [selectedPlan, setSelectedPlan] = useState<'pro' | 'career_monthly' | 'career_annual'>('career_annual')
  const [source, setSource] = useState<string>('')

  useEffect(() => {
    const plan = searchParams.get('plan')
    const src = searchParams.get('source')
    if (plan) {
      if (plan === 'pro') setSelectedPlan('pro')
      else if (plan === 'career') setSelectedPlan('career_annual')
    }
    if (src) setSource(src)
  }, [searchParams])

  async function handleUpgrade() {
    if (!user) return
    
    setLoading(true)
    try {
      const response = await api.post('/billing/upgrade', {
        plan: selectedPlan === 'pro' ? 'pro' : 'career',
        cycle: selectedPlan === 'career_monthly' ? 'monthly' : 'annual',
        source: source || undefined,
      })
      
      // Redirect to Stripe Checkout
      if (response.data.checkout_url) {
        window.location.href = response.data.checkout_url
      }
    } catch (error: any) {
      console.error('Upgrade failed:', error)
      alert(error.response?.data?.detail || 'Failed to start upgrade. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="animate-pulse space-y-8">
            <div className="h-8 bg-slate-200 rounded w-1/3"></div>
            <div className="grid md:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-96 bg-slate-200 rounded-2xl"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-navy-900 mb-4">Choose Your Plan</h1>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto">
            Invest in your career with intelligent tools and market insights
          </p>
        </div>

        {/* Plan Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {/* FREE Plan */}
          <div className="bg-white rounded-2xl shadow-lg p-8 border-2 border-slate-200">
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-navy-900 mb-2">FREE</h3>
              <p className="text-slate-600">For casual browsers</p>
            </div>
            <div className="mb-6">
              <span className="text-4xl font-bold text-navy-900">$0</span>
              <span className="text-slate-600">/month</span>
            </div>
            <ul className="space-y-4 mb-8">
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">5 applications/month</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Basic job matching</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Application tracking</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Career dashboard (basic)</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">❌</span>
                <span className="text-slate-400">AI CV tailoring</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">❌</span>
                <span className="text-slate-400">Salary benchmarking</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">❌</span>
                <span className="text-slate-400">Promotion alerts</span>
              </li>
            </ul>
            <button
              disabled
              className="w-full bg-slate-200 text-slate-600 font-semibold py-3 px-6 rounded-xl cursor-not-allowed"
            >
              Current Plan
            </button>
          </div>

          {/* PRO Plan */}
          <div className={`bg-white rounded-2xl shadow-lg p-8 border-2 ${selectedPlan === 'pro' ? 'border-teal-500 ring-4 ring-teal-200' : 'border-slate-200'}`}>
            <div className="mb-6">
              <h3 className="text-2xl font-bold text-navy-900 mb-2">PRO</h3>
              <p className="text-slate-600">For active job seekers</p>
            </div>
            <div className="mb-6">
              <span className="text-4xl font-bold text-navy-900">$29</span>
              <span className="text-slate-600">/month</span>
            </div>
            <ul className="space-y-4 mb-8">
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Unlimited applications</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">AI CV tailoring</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">AI cover letters</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Auto-apply extension</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Full salary benchmarking</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Quarterly salary reviews</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">❌</span>
                <span className="text-slate-400">Promotion readiness alerts</span>
              </li>
              <li className="flex items-start">
                <span className="text-red-500 mr-2">❌</span>
                <span className="text-slate-400">Passive job alerts</span>
              </li>
            </ul>
            <button
              onClick={handleUpgrade}
              disabled={loading || user?.subscription_plan === 'pro'}
              className={`w-full font-semibold py-3 px-6 rounded-xl transition-colors ${
                user?.subscription_plan === 'pro'
                  ? 'bg-slate-200 text-slate-600 cursor-not-allowed'
                  : loading
                  ? 'bg-teal-400 text-white cursor-wait'
                  : 'bg-teal-500 hover:bg-teal-600 text-white'
              }`}
            >
              {loading ? 'Processing...' : user?.subscription_plan === 'pro' ? 'Current Plan' : 'Start PRO Trial'}
            </button>
          </div>

          {/* CAREER Plan */}
          <div className={`bg-gradient-to-b from-navy-900 to-navy-800 rounded-2xl shadow-lg p-8 border-2 ${selectedPlan.includes('career') ? 'border-teal-400 ring-4 ring-teal-200' : 'border-navy-700'} text-white relative`}>
            <div className="absolute top-4 right-4 bg-teal-500 text-white text-xs font-bold px-3 py-1 rounded-full">
              BEST VALUE
            </div>
            <div className="mb-6">
              <h3 className="text-2xl font-bold mb-2">CAREER</h3>
              <p className="text-slate-300">For career growth</p>
            </div>
            <div className="mb-6">
              <div className="flex items-baseline">
                <span className="text-4xl font-bold">$19</span>
                <span className="text-slate-300 ml-2">/month</span>
              </div>
              <p className="text-sm text-teal-300 mt-2">or $149/year (save 35%)</p>
            </div>
            <ul className="space-y-4 mb-8">
              <li className="flex items-start">
                <span className="text-teal-400 mr-2">✅</span>
                <span>Everything in PRO</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-400 mr-2">✅</span>
                <span>Passive job alerts</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-400 mr-2">✅</span>
                <span>Promotion readiness alerts</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-400 mr-2">✅</span>
                <span>Annual career report PDF</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-400 mr-2">✅</span>
                <span>Skill gap analysis</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-400 mr-2">✅</span>
                <span>Market intelligence dashboard</span>
              </li>
              <li className="flex items-start">
                <span className="text-teal-400 mr-2">✅</span>
                <span>Negotiation coaching</span>
              </li>
            </ul>
            
            {/* Cycle Toggle */}
            <div className="flex bg-navy-700 rounded-lg p-1 mb-6">
              <button
                onClick={() => setSelectedPlan('career_monthly')}
                className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedPlan === 'career_monthly'
                    ? 'bg-teal-500 text-white'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setSelectedPlan('career_annual')}
                className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                  selectedPlan === 'career_annual'
                    ? 'bg-teal-500 text-white'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Annual <span className="text-xs">(-35%)</span>
              </button>
            </div>
            
            <button
              onClick={handleUpgrade}
              disabled={loading || user?.subscription_plan === 'career'}
              className={`w-full font-semibold py-3 px-6 rounded-xl transition-colors ${
                user?.subscription_plan === 'career'
                  ? 'bg-slate-200 text-slate-600 cursor-not-allowed'
                  : loading
                  ? 'bg-teal-400 text-white cursor-wait'
                  : 'bg-teal-500 hover:bg-teal-600 text-white'
              }`}
            >
              {loading ? 'Processing...' : user?.subscription_plan === 'career' ? 'Current Plan' : `Start ${selectedPlan === 'career_annual' ? '$149/year' : '$19/month'}`}
            </button>
          </div>
        </div>

        {/* Feature Comparison */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-12">
          <h2 className="text-2xl font-bold text-navy-900 mb-6 text-center">Compare Features</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-4 px-4 font-semibold text-slate-700">Feature</th>
                  <th className="text-center py-4 px-4 font-semibold text-slate-700">FREE</th>
                  <th className="text-center py-4 px-4 font-semibold text-teal-600">PRO</th>
                  <th className="text-center py-4 px-4 font-semibold text-navy-900">CAREER</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-100">
                  <td className="py-4 px-4 text-slate-700">Applications/month</td>
                  <td className="text-center py-4 px-4 text-slate-600">5</td>
                  <td className="text-center py-4 px-4 text-teal-600 font-medium">Unlimited</td>
                  <td className="text-center py-4 px-4 text-navy-900 font-medium">Unlimited</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-4 px-4 text-slate-700">AI CV Tailoring</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-teal-600">✅</td>
                  <td className="text-center py-4 px-4 text-navy-900">✅</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-4 px-4 text-slate-700">Auto-Apply Extension</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-teal-600">✅</td>
                  <td className="text-center py-4 px-4 text-navy-900">✅</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-4 px-4 text-slate-700">Salary Benchmarking</td>
                  <td className="text-center py-4 px-4 text-slate-400">Teaser</td>
                  <td className="text-center py-4 px-4 text-teal-600">✅</td>
                  <td className="text-center py-4 px-4 text-navy-900">✅</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-4 px-4 text-slate-700">Promotion Alerts</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-navy-900 font-medium">✅</td>
                </tr>
                <tr className="border-b border-slate-100">
                  <td className="py-4 px-4 text-slate-700">Passive Job Alerts</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-navy-900 font-medium">✅</td>
                </tr>
                <tr>
                  <td className="py-4 px-4 text-slate-700">Annual Career Report</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-slate-400">❌</td>
                  <td className="text-center py-4 px-4 text-navy-900 font-medium">✅</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-navy-900 mb-6 text-center">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <div className="bg-white rounded-xl p-6">
              <h3 className="font-semibold text-navy-900 mb-2">Can I cancel anytime?</h3>
              <p className="text-slate-600">Yes! You can cancel your subscription at any time. Your access will continue until the end of your billing period.</p>
            </div>
            <div className="bg-white rounded-xl p-6">
              <h3 className="font-semibold text-navy-900 mb-2">What happens if I find a job?</h3>
              <p className="text-slate-600">Great question! When you land a job, we'll offer you to downgrade to CAREER tier to track your career growth long-term. Many users stay for the salary reviews and promotion alerts.</p>
            </div>
            <div className="bg-white rounded-xl p-6">
              <h3 className="font-semibold text-navy-900 mb-2">Is there a free trial?</h3>
              <p className="text-slate-600">PRO tier includes a 7-day free trial. CAREER tier can be canceled anytime within the first 30 days for a full refund.</p>
            </div>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  )
}

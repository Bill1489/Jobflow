"use client"

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth'
import { api } from '@/lib/api'
import { Navbar } from '@/components/Navbar'
import { Footer } from '@/components/Footer'

interface CareerProgress {
  id: number
  user_id: number
  current_company: string
  current_title: string
  current_salary: number
  currency: string
  seniority_level: string
  started_at: string
  location: string
  next_seniority_level: string
  months_in_role: number
  promotions_count: number
  skills_gained: string[]
  leadership_projects: number
  next_salary_review_date: string
}

interface SalaryPosition {
  percentile: number
  is_below_market: boolean
  underpaid_percentage: number
  market_avg: number
  market_top_25: number
}

interface DashboardData {
  has_career_tracking: boolean
  career?: CareerProgress
  salary_position?: SalaryPosition
  promotion_ready?: boolean
  total_growth?: {
    absolute: number
    percentage: number
  }
  message?: string
}

export default function CareerDashboard() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<DashboardData | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'salary' | 'progression' | 'goals'>('overview')

  useEffect(() => {
    fetchDashboard()
  }, [])

  async function fetchDashboard() {
    try {
      const response = await api.get('/career/dashboard')
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch career dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="max-w-7xl mx-auto px-4 py-12">
          <div className="animate-pulse space-y-8">
            <div className="h-8 bg-slate-200 rounded w-1/3"></div>
            <div className="h-64 bg-slate-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!data?.has_career_tracking) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Navbar />
        <div className="max-w-3xl mx-auto px-4 py-12">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <h1 className="text-3xl font-bold text-navy-900 mb-4">Start Your Career Tracking</h1>
            <p className="text-slate-600 mb-8">
              Track your career progression, get salary benchmarks, and receive promotion alerts.
            </p>
            <button
              onClick={() => window.location.href = '/onboarding'}
              className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 px-8 rounded-xl transition-colors"
            >
              Get Started
            </button>
          </div>
        </div>
      </div>
    )
  }

  const career = data.career!

  return (
    <div className="min-h-screen bg-slate-50">
      <Navbar />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-navy-900 mb-2">Career Dashboard</h1>
          <p className="text-slate-600">Track your progress and plan your next move</p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-2 mb-8 border-b border-slate-200">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'salary', label: 'Salary Check' },
            { id: 'progression', label: 'Progression' },
            { id: 'goals', label: 'Goals' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-6 py-3 font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-teal-600 border-b-2 border-teal-600'
                  : 'text-slate-600 hover:text-navy-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Current Role Card */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-bold text-navy-900 mb-4">Current Role</h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-slate-600 mb-1">Company</p>
                  <p className="text-lg font-semibold text-navy-900">{career.current_company}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">Title</p>
                  <p className="text-lg font-semibold text-navy-900">{career.current_title}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">Salary</p>
                  <p className="text-lg font-semibold text-navy-900">£{career.current_salary.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">Location</p>
                  <p className="text-lg font-semibold text-navy-900">{career.location}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">Started</p>
                  <p className="text-lg font-semibold text-navy-900">
                    {new Date(career.started_at).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-600 mb-1">Tenure</p>
                  <p className="text-lg font-semibold text-navy-900">{career.months_in_role} months</p>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <p className="text-sm text-slate-600 mb-2">Promotions</p>
                <p className="text-3xl font-bold text-teal-500">{career.promotions_count}</p>
              </div>
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <p className="text-sm text-slate-600 mb-2">Skills Gained</p>
                <p className="text-3xl font-bold text-teal-500">{career.skills_gained.length}</p>
              </div>
              <div className="bg-white rounded-2xl shadow-lg p-6">
                <p className="text-sm text-slate-600 mb-2">Leadership Projects</p>
                <p className="text-3xl font-bold text-teal-500">{career.leadership_projects}</p>
              </div>
            </div>

            {/* Next Review */}
            <div className="bg-gradient-to-r from-navy-900 to-navy-800 rounded-2xl shadow-lg p-6 text-white">
              <h3 className="text-lg font-semibold mb-2">Next Salary Review</h3>
              <p className="text-2xl font-bold">
                {career.next_salary_review_date
                  ? new Date(career.next_salary_review_date).toLocaleDateString('en-GB', { month: 'long', year: 'numeric' })
                  : 'Not scheduled'}
              </p>
            </div>
          </div>
        )}

        {/* Salary Tab */}
        {activeTab === 'salary' && (
          <SalaryCheckTab user={user!} />
        )}

        {/* Progression Tab */}
        {activeTab === 'progression' && (
          <ProgressionTab user={user!} career={career} />
        )}

        {/* Goals Tab */}
        {activeTab === 'goals' && (
          <GoalsTab user={user!} />
        )}
      </div>

      <Footer />
    </div>
  )
}

// Salary Check Tab Component
function SalaryCheckTab({ user }: { user: any }) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    fetchSalaryCheck()
  }, [])

  async function fetchSalaryCheck() {
    try {
      const response = await api.get('/career/salary-check')
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch salary check:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="animate-pulse h-64 bg-white rounded-2xl"></div>
  }

  if (data?.upgrade_required) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="max-w-md mx-auto">
          <div className="text-6xl mb-4">🔒</div>
          <h3 className="text-2xl font-bold text-navy-900 mb-4">Unlock Full Salary Benchmarking</h3>
          <p className="text-slate-600 mb-6">
            See how your salary compares to the market, discover similar roles, and know your worth.
          </p>
          <div className="bg-slate-50 rounded-xl p-6 mb-6">
            <ul className="text-left space-y-3">
              <li className="flex items-center">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Market average comparison</span>
              </li>
              <li className="flex items-center">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Top 25% and top 10% benchmarks</span>
              </li>
              <li className="flex items-center">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Similar higher-paying roles</span>
              </li>
              <li className="flex items-center">
                <span className="text-teal-500 mr-2">✅</span>
                <span className="text-slate-700">Quarterly salary reviews</span>
              </li>
            </ul>
          </div>
          <button
            onClick={() => window.location.href = '/billing/upgrade?plan=career'}
            className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 px-8 rounded-xl transition-colors"
          >
            Unlock for {data.upgrade_price}
          </button>
        </div>
      </div>
    )
  }

  const isBelow = data?.is_below_market

  return (
    <div className="space-y-6">
      <div className={`rounded-2xl shadow-lg p-8 ${isBelow ? 'bg-gradient-to-r from-red-50 to-orange-50' : 'bg-gradient-to-r from-green-50 to-teal-50'}`}>
        <h3 className={`text-2xl font-bold mb-4 ${isBelow ? 'text-red-700' : 'text-green-700'}`}>
          {isBelow ? '⚠️ Below Market Average' : '✅ Competitive Salary'}
        </h3>
        
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl p-6">
            <p className="text-sm text-slate-600 mb-2">Your Salary</p>
            <p className="text-3xl font-bold text-navy-900">£{data.current_salary?.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-xl p-6">
            <p className="text-sm text-slate-600 mb-2">Market Average</p>
            <p className={`text-3xl font-bold ${isBelow ? 'text-red-600' : 'text-green-600'}`}>
              £{data.market_avg?.toLocaleString()}
            </p>
          </div>
        </div>

        {data.underpaid_percentage && data.underpaid_percentage > 0 && (
          <div className="bg-white rounded-xl p-6 mb-6">
            <p className="text-sm text-slate-600 mb-2">You're Underpaid By</p>
            <p className="text-4xl font-bold text-red-600">{data.underpaid_percentage}%</p>
            <p className="text-slate-600">
              That's £{(data.market_avg - data.current_salary).toLocaleString()} per year
            </p>
          </div>
        )}

        {data.percentile && (
          <div>
            <p className="text-sm text-slate-600 mb-2">Market Position</p>
            <div className="bg-white rounded-full h-6 overflow-hidden">
              <div
                className="bg-teal-500 h-full transition-all"
                style={{ width: `${data.percentile}%` }}
              ></div>
            </div>
            <p className="text-sm text-slate-600 mt-2">Top {data.percentile}% of earners</p>
          </div>
        )}
      </div>
    </div>
  )
}

// Progression Tab Component
function ProgressionTab({ user, career }: { user: any; career: CareerProgress }) {
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    fetchProgression()
  }, [])

  async function fetchProgression() {
    try {
      const response = await api.get('/career/progression')
      setData(response.data)
    } catch (error) {
      console.error('Failed to fetch progression:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="animate-pulse h-64 bg-white rounded-2xl"></div>
  }

  if (data?.upgrade_required) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
        <div className="max-w-md mx-auto">
          <div className="text-6xl mb-4">🎯</div>
          <h3 className="text-2xl font-bold text-navy-900 mb-4">See Your Promotion Opportunities</h3>
          <p className="text-slate-600 mb-6">
            Unlock salary benchmarks for your next level and discover available roles.
          </p>
          <button
            onClick={() => window.location.href = '/billing/upgrade?plan=career'}
            className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 px-8 rounded-xl transition-colors"
          >
            Upgrade to CAREER
          </button>
        </div>
      </div>
    )
  }

  const ready = data?.ready
  const score = data?.score || 0

  return (
    <div className="space-y-6">
      <div className={`rounded-2xl shadow-lg p-8 ${ready ? 'bg-gradient-to-r from-green-50 to-teal-50' : 'bg-gradient-to-r from-blue-50 to-indigo-50'}`}>
        <h3 className={`text-2xl font-bold mb-4 ${ready ? 'text-green-700' : 'text-blue-700'}`}>
          {ready ? '🎉 You\'re Ready for Promotion!' : '📈 Building Towards Promotion'}
        </h3>

        <div className="mb-6">
          <p className="text-sm text-slate-600 mb-2">Readiness Score</p>
          <div className="flex items-end space-x-4">
            <p className="text-5xl font-bold text-navy-900">{score}</p>
            <p className="text-slate-600 mb-2">out of 100</p>
          </div>
          <div className="bg-white rounded-full h-4 mt-4 overflow-hidden">
            <div
              className={`h-full transition-all ${ready ? 'bg-green-500' : 'bg-blue-500'}`}
              style={{ width: `${score}%` }}
            ></div>
          </div>
        </div>

        {ready && data?.market_salary && (
          <div className="bg-white rounded-xl p-6">
            <p className="text-sm text-slate-600 mb-2">Market Salary for {career.next_seniority_level}</p>
            <p className="text-3xl font-bold text-teal-600">£{data.market_salary.toLocaleString()}</p>
            <p className="text-slate-600">
              Potential increase: £{(data.market_salary - career.current_salary).toLocaleString()}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

// Goals Tab Component
function GoalsTab({ user }: { user: any }) {
  const [goals, setGoals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [newGoal, setNewGoal] = useState({
    goal_type: 'promotion',
    target_title: '',
    target_salary: '',
    target_company: '',
    target_date: '',
  })

  useEffect(() => {
    fetchGoals()
  }, [])

  async function fetchGoals() {
    try {
      const response = await api.get('/career/goals')
      setGoals(response.data)
    } catch (error) {
      console.error('Failed to fetch goals:', error)
    } finally {
      setLoading(false)
    }
  }

  async function createGoal(e: React.FormEvent) {
    e.preventDefault()
    try {
      await api.post('/career/goals', {
        ...newGoal,
        target_salary: newGoal.target_salary ? parseInt(newGoal.target_salary) : null,
      })
      fetchGoals()
      setShowForm(false)
      setNewGoal({ goal_type: 'promotion', target_title: '', target_salary: '', target_company: '', target_date: '' })
    } catch (error) {
      console.error('Failed to create goal:', error)
    }
  }

  if (loading) {
    return <div className="animate-pulse h-64 bg-white rounded-2xl"></div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-bold text-navy-900">Career Goals</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
        >
          {showForm ? 'Cancel' : '+ Add Goal'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={createGoal} className="bg-white rounded-2xl shadow-lg p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Goal Type</label>
            <select
              value={newGoal.goal_type}
              onChange={(e) => setNewGoal({ ...newGoal, goal_type: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-4 py-2"
            >
              <option value="promotion">Promotion</option>
              <option value="salary">Salary Increase</option>
              <option value="skills">Skills Development</option>
              <option value="company">Dream Company</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Target Title</label>
            <input
              type="text"
              value={newGoal.target_title}
              onChange={(e) => setNewGoal({ ...newGoal, target_title: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-4 py-2"
              placeholder="e.g., Senior Software Engineer"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Target Salary</label>
            <input
              type="number"
              value={newGoal.target_salary}
              onChange={(e) => setNewGoal({ ...newGoal, target_salary: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-4 py-2"
              placeholder="e.g., 100000"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Target Date</label>
            <input
              type="date"
              value={newGoal.target_date}
              onChange={(e) => setNewGoal({ ...newGoal, target_date: e.target.value })}
              className="w-full border border-slate-300 rounded-lg px-4 py-2"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 rounded-lg transition-colors"
          >
            Create Goal
          </button>
        </form>
      )}

      <div className="space-y-4">
        {goals.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
            <p className="text-slate-600">No goals yet. Add your first career goal!</p>
          </div>
        ) : (
          goals.map((goal) => (
            <div key={goal.id} className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <p className="text-sm text-teal-600 font-medium uppercase">{goal.goal_type}</p>
                  <h4 className="text-lg font-bold text-navy-900">{goal.target_title || 'Career Goal'}</h4>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                  goal.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-700'
                }`}>
                  {goal.status}
                </span>
              </div>
              {goal.target_salary && (
                <p className="text-slate-600 mb-2">Target: £{goal.target_salary.toLocaleString()}</p>
              )}
              {goal.target_date && (
                <p className="text-slate-600 mb-4">
                  Target Date: {new Date(goal.target_date).toLocaleDateString('en-GB')}
                </p>
              )}
              {goal.progress !== undefined && (
                <div>
                  <div className="flex justify-between text-sm text-slate-600 mb-2">
                    <span>Progress</span>
                    <span>{goal.progress}%</span>
                  </div>
                  <div className="bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-teal-500 h-full rounded-full transition-all"
                      style={{ width: `${goal.progress}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';

interface CV {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  summary?: string;
  experience: any[];
  education: any[];
  skills: string[];
  template_id: string;
  is_ai_generated: boolean;
  created_at: string;
}

interface ParsedCV {
  personal_info: any;
  summary: string;
  experience: any[];
  education: any[];
  skills: string[];
  suggestions: string[];
}

export default function CVBuilderPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'landing' | 'upload' | 'build' | 'edit'>('landing');
  const [cvs, setCvs] = useState<CV[]>([]);
  const [selectedCV, setSelectedCV] = useState<CV | null>(null);
  const [parsedCV, setParsedCV] = useState<ParsedCV | null>(null);
  const [uploading, setUploading] = useState(false);
  const [skillInput, setSkillInput] = useState('');
  
  const [cvData, setCvData] = useState({
    full_name: '',
    email: user?.email || '',
    phone: '',
    location: '',
    linkedin_url: '',
    portfolio_url: '',
    summary: '',
    experience: [{ company: '', role: '', start_date: '', end_date: '', description: '' }],
    education: [{ institution: '', degree: '', field: '', graduation_year: '' }],
    skills: [] as string[],
    certifications: [] as any[],
    projects: [] as any[],
    template_id: 'modern'
  });

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadCVs();
    }
  }, [user]);

  async function loadCVs() {
    try {
      const res = await fetch('/api/v1/cvs');
      if (res.ok) {
        const data = await res.json();
        setCvs(data.cvs);
      }
    } catch (err) {
      console.error('Failed to load CVs:', err);
    }
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please upload a PDF or DOCX file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File must be less than 5MB');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch('/api/v1/cvs/upload', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Failed to upload CV');
      }

      const data = await res.json();
      
      // Store parsed data
      setParsedCV(data.parsed_data);
      
      // Pre-fill form with parsed data
      const parsed = data.parsed_data;
      setCvData({
        full_name: parsed.personal_info?.full_name || '',
        email: parsed.personal_info?.email || user?.email || '',
        phone: parsed.personal_info?.phone || '',
        location: parsed.personal_info?.location || '',
        linkedin_url: parsed.personal_info?.linkedin_url || '',
        portfolio_url: parsed.personal_info?.portfolio_url || '',
        summary: parsed.summary || '',
        experience: parsed.experience?.length > 0 ? parsed.experience : [{ company: '', role: '', start_date: '', end_date: '', description: '' }],
        education: parsed.education?.length > 0 ? parsed.education : [{ institution: '', degree: '', field: '', graduation_year: '' }],
        skills: parsed.skills || [],
        certifications: parsed.certifications || [],
        projects: [],
        template_id: 'modern'
      });

      toast.success('CV uploaded and parsed! Review the info below.');
      setView('edit');
      
    } catch (err: any) {
      console.error('Upload error:', err);
      toast.error(err.message || 'Failed to upload CV');
    } finally {
      setUploading(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (cvData.experience.length === 0 || cvData.skills.length === 0) {
      toast.error('Please add at least one experience and skill first');
      return;
    }

    const loadingToast = toast.loading('Generating professional summary...');
    
    try {
      const res = await fetch('/api/v1/cvs/generate-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          experience: cvData.experience,
          skills: cvData.skills,
          target_role: 'Software Engineer'
        })
      });

      if (res.ok) {
        const data = await res.json();
        setCvData(prev => ({ ...prev, summary: data.summary }));
        toast.success('AI-generated summary created!', { id: loadingToast });
      } else {
        toast.error('Failed to generate summary', { id: loadingToast });
      }
    } catch (err) {
      toast.error('Failed to generate summary', { id: loadingToast });
    }
  };

  const handleSaveCV = async () => {
    if (!cvData.full_name || !cvData.email) {
      toast.error('Name and email are required');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch('/api/v1/cvs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(cvData)
      });

      if (res.ok) {
        toast.success('CV saved successfully!');
        loadCVs();
        setView('landing');
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to save CV');
      }
    } catch (err) {
      toast.error('Failed to save CV');
    } finally {
      setLoading(false);
    }
  };

  const handleAddExperience = () => {
    setCvData(prev => ({
      ...prev,
      experience: [...prev.experience, { company: '', role: '', start_date: '', end_date: '', description: '' }]
    }));
  };

  const handleUpdateExperience = (index: number, field: string, value: string) => {
    const updated = cvData.experience.map((exp, i) => 
      i === index ? { ...exp, [field]: value } : exp
    );
    setCvData(prev => ({ ...prev, experience: updated }));
  };

  const handleRemoveExperience = (index: number) => {
    setCvData(prev => ({
      ...prev,
      experience: prev.experience.filter((_, i) => i !== index)
    }));
  };

  const handleAddEducation = () => {
    setCvData(prev => ({
      ...prev,
      education: [...prev.education, { institution: '', degree: '', field: '', graduation_year: '' }]
    }));
  };

  const handleUpdateEducation = (index: number, field: string, value: string) => {
    const updated = cvData.education.map((edu, i) => 
      i === index ? { ...edu, [field]: value } : edu
    );
    setCvData(prev => ({ ...prev, education: updated }));
  };

  const handleRemoveEducation = (index: number) => {
    setCvData(prev => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== index)
    }));
  };

  const handleAddSkill = () => {
    if (skillInput.trim() && !cvData.skills.includes(skillInput.trim())) {
      setCvData(prev => ({
        ...prev,
        skills: [...prev.skills, skillInput.trim()]
      }));
      setSkillInput('');
    }
  };

  const handleRemoveSkill = (skill: string) => {
    setCvData(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s !== skill)
    }));
  };

  // Loading state
  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500"></div>
      </div>
    );
  }

  // Landing page - choose upload or build
  if (view === 'landing') {
    return (
      <div className="min-h-screen bg-slate-50">
        {/* Header */}
        <header className="bg-white shadow-sm sticky top-0 z-40">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-slate-900">CV Builder</h1>
              <button
                onClick={() => router.push('/dashboard')}
                className="text-sm text-slate-600 hover:text-navy-900"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
          {/* Hero */}
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Build a Professional CV
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Choose how you want to create your CV. We'll help you make it stand out.
            </p>
          </div>

          {/* Two Options */}
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            {/* Option 1: Upload CV */}
            <div 
              onClick={() => setView('upload')}
              className="bg-white rounded-2xl shadow-xl p-8 border-2 border-transparent hover:border-teal-500 transition-all cursor-pointer group"
            >
              <div className="w-16 h-16 bg-teal-100 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-teal-200 transition-colors">
                <svg className="w-8 h-8 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Upload Your CV</h3>
              <p className="text-slate-600 mb-6">
                Upload your existing CV (PDF or DOCX). We'll parse it and help you improve it with AI.
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>Fastest option (2-3 minutes)</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>We extract your info automatically</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>AI suggests improvements</span>
                </li>
              </ul>
              <div className="mt-6 text-teal-600 font-semibold group-hover:text-teal-700">
                Upload CV →
              </div>
            </div>

            {/* Option 2: Build from Scratch */}
            <div 
              onClick={() => setView('build')}
              className="bg-white rounded-2xl shadow-xl p-8 border-2 border-transparent hover:border-navy-900 transition-all cursor-pointer group"
            >
              <div className="w-16 h-16 bg-navy-100 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-navy-200 transition-colors">
                <svg className="w-8 h-8 text-navy-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">Build from Scratch</h3>
              <p className="text-slate-600 mb-6">
                Start fresh with our guided form. Perfect if you don't have a CV or want complete control.
              </p>
              <ul className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>Complete control over content</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>AI generates professional summary</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-green-500 mt-1">✓</span>
                  <span>Step-by-step guidance</span>
                </li>
              </ul>
              <div className="mt-6 text-navy-900 font-semibold group-hover:text-navy-800">
                Build from Scratch →
              </div>
            </div>
          </div>

          {/* Existing CVs */}
          {cvs.length > 0 && (
            <div>
              <h3 className="text-xl font-bold text-slate-900 mb-4">Your Existing CVs</h3>
              <div className="space-y-4">
                {cvs.map((cv) => (
                  <div key={cv.id} className="bg-white border border-slate-200 rounded-xl p-6 hover:border-teal-300 transition-colors">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-lg font-semibold text-slate-900">{cv.full_name}</h4>
                        <p className="text-sm text-slate-600">{cv.email}</p>
                        <div className="mt-2 flex items-center space-x-4 text-xs text-slate-500">
                          <span>📄 {cv.template_id}</span>
                          <span>📅 {new Date(cv.created_at).toLocaleDateString()}</span>
                          {cv.is_ai_generated && <span>✨ AI-Generated</span>}
                        </div>
                      </div>
                      <div className="flex space-x-3">
                        <button 
                          onClick={() => {
                            setSelectedCV(cv);
                            setCvData({
                              full_name: cv.full_name,
                              email: cv.email,
                              phone: cv.phone || '',
                              location: cv.location || '',
                              linkedin_url: cv.linkedin_url || '',
                              portfolio_url: cv.portfolio_url || '',
                              summary: cv.summary || '',
                              experience: cv.experience,
                              education: cv.education,
                              skills: cv.skills,
                              certifications: cv.certifications || [],
                              projects: [],
                              template_id: cv.template_id
                            });
                            setView('edit');
                          }}
                          className="px-4 py-2 text-sm text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                        >
                          Edit
                        </button>
                        <button className="px-4 py-2 text-sm text-navy-900 bg-navy-900 text-white rounded-lg hover:bg-navy-800 transition-colors">
                          Download PDF
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      </div>
    );
  }

  // Upload view
  if (view === 'upload') {
    return (
      <div className="min-h-screen bg-slate-50">
        <header className="bg-white shadow-sm sticky top-0 z-40">
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-4">
            <button
              onClick={() => setView('landing')}
              className="text-sm text-slate-600 hover:text-navy-900 flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back</span>
            </button>
          </div>
        </header>

        <main className="max-w-3xl mx-auto px-4 sm:px-6 py-12">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-teal-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-teal-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Upload Your CV</h2>
              <p className="text-slate-600">
                We'll parse it and help you improve it with AI
              </p>
            </div>

            {uploading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
                <p className="text-slate-600">Parsing your CV...</p>
              </div>
            ) : (
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:border-teal-500 transition-colors">
                <input
                  type="file"
                  id="cv-upload"
                  accept=".pdf,.docx"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <label htmlFor="cv-upload" className="cursor-pointer">
                  <svg className="w-16 h-16 text-slate-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-lg font-semibold text-slate-900 mb-2">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-sm text-slate-600 mb-4">
                    PDF or DOCX (max 5MB)
                  </p>
                  <div className="inline-block px-6 py-3 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-semibold">
                    Select File
                  </div>
                </label>
              </div>
            )}

            <div className="mt-8 bg-slate-50 rounded-xl p-6">
              <h4 className="font-semibold text-slate-900 mb-3">What happens next?</h4>
              <ol className="space-y-2 text-sm text-slate-600">
                <li className="flex items-start space-x-2">
                  <span className="font-semibold">1.</span>
                  <span>We extract your personal info, experience, education, and skills</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="font-semibold">2.</span>
                  <span>You review and edit the parsed information</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="font-semibold">3.</span>
                  <span>AI suggests improvements and can generate a professional summary</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="font-semibold">4.</span>
                  <span>Download as a polished, professional CV</span>
                </li>
              </ol>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Build from scratch or Edit view
  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex justify-between items-center">
            <button
              onClick={() => setView('landing')}
              className="text-sm text-slate-600 hover:text-navy-900 flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back</span>
            </button>
            <h1 className="text-xl font-bold text-slate-900">
              {view === 'edit' ? 'Edit CV' : 'Build Your CV'}
            </h1>
            <div className="w-20"></div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* Show suggestions if uploaded */}
        {parsedCV && parsedCV.suggestions.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-6">
            <h3 className="font-semibold text-amber-900 mb-3 flex items-center space-x-2">
              <span>💡</span>
              <span>AI Suggestions to Improve Your CV</span>
            </h3>
            <ul className="space-y-2 text-sm text-amber-800">
              {parsedCV.suggestions.map((suggestion: string, i: number) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-amber-600 mt-1">•</span>
                  <span>{suggestion}</span>
                </li>
              ))}
            </ul>
            <button
              onClick={handleGenerateSummary}
              className="mt-4 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors text-sm font-medium"
            >
              ✨ Generate Professional Summary with AI
            </button>
          </div>
        )}

        {/* CV Form */}
        <div className="space-y-6">
          {/* Personal Info */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-xl font-bold text-slate-900 mb-6">Personal Information</h3>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Full Name *</label>
                <input
                  type="text"
                  value={cvData.full_name}
                  onChange={(e) => setCvData(prev => ({ ...prev, full_name: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                  placeholder="John Doe"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Email *</label>
                <input
                  type="email"
                  value={cvData.email}
                  onChange={(e) => setCvData(prev => ({ ...prev, email: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                  placeholder="john@example.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Phone</label>
                <input
                  type="tel"
                  value={cvData.phone}
                  onChange={(e) => setCvData(prev => ({ ...prev, phone: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                  placeholder="+44 7700 900000"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Location</label>
                <input
                  type="text"
                  value={cvData.location}
                  onChange={(e) => setCvData(prev => ({ ...prev, location: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                  placeholder="London, UK"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">LinkedIn URL</label>
                <input
                  type="url"
                  value={cvData.linkedin_url}
                  onChange={(e) => setCvData(prev => ({ ...prev, linkedin_url: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                  placeholder="https://linkedin.com/in/johndoe"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Portfolio URL</label>
                <input
                  type="url"
                  value={cvData.portfolio_url}
                  onChange={(e) => setCvData(prev => ({ ...prev, portfolio_url: e.target.value }))}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                  placeholder="https://johndoe.com"
                />
              </div>
            </div>
          </div>

          {/* Professional Summary */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-slate-900">Professional Summary</h3>
              <button
                onClick={handleGenerateSummary}
                disabled={cvData.experience.length === 0 || cvData.skills.length === 0}
                className="px-4 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors text-sm font-medium disabled:opacity-50 flex items-center space-x-2"
              >
                <span>✨</span>
                <span>AI Generate</span>
              </button>
            </div>
            
            <textarea
              value={cvData.summary}
              onChange={(e) => setCvData(prev => ({ ...prev, summary: e.target.value }))}
              rows={4}
              className="w-full px-4 py-3 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none resize-none"
              placeholder="Write a compelling 3-4 sentence summary about your experience and career goals..."
            />
            <p className="mt-2 text-sm text-slate-600">
              Tip: Use the AI Generate button to create a professional summary automatically
            </p>
          </div>

          {/* Experience */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-slate-900">Work Experience</h3>
              <button
                onClick={handleAddExperience}
                className="px-4 py-2 text-teal-600 hover:bg-teal-50 rounded-lg transition-colors text-sm font-medium flex items-center space-x-2"
              >
                <span>+</span>
                <span>Add Position</span>
              </button>
            </div>
            
            <div className="space-y-6">
              {cvData.experience.map((exp, index) => (
                <div key={index} className="border border-slate-200 rounded-xl p-6 relative">
                  {cvData.experience.length > 1 && (
                    <button
                      onClick={() => handleRemoveExperience(index)}
                      className="absolute top-4 right-4 text-red-600 hover:text-red-700 text-sm"
                    >
                      Remove
                    </button>
                  )}
                  
                  <div className="grid md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Company</label>
                      <input
                        type="text"
                        value={exp.company}
                        onChange={(e) => handleUpdateExperience(index, 'company', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                        placeholder="Google"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Role</label>
                      <input
                        type="text"
                        value={exp.role}
                        onChange={(e) => handleUpdateExperience(index, 'role', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                        placeholder="Software Engineer"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">Start Date</label>
                      <input
                        type="text"
                        value={exp.start_date}
                        onChange={(e) => handleUpdateExperience(index, 'start_date', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                        placeholder="Jan 2020"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">End Date</label>
                      <input
                        type="text"
                        value={exp.end_date}
                        onChange={(e) => handleUpdateExperience(index, 'end_date', e.target.value)}
                        className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                        placeholder="Present"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">Description</label>
                    <textarea
                      value={exp.description}
                      onChange={(e) => handleUpdateExperience(index, 'description', e.target.value)}
                      rows={3}
                      className="w-full px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none resize-none"
                      placeholder="• Built X that achieved Y...&#10;• Reduced Z by 40% through..."
                    />
                    <p className="mt-1 text-xs text-slate-500">
                      Tip: Use bullet points with measurable achievements (numbers, percentages, impact)
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Skills */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-xl font-bold text-slate-900 mb-6">Skills</h3>
            
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={skillInput}
                onChange={(e) => setSkillInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSkill())}
                className="flex-1 px-4 py-2 border-2 border-slate-200 rounded-lg focus:border-teal-500 focus:outline-none"
                placeholder="Add a skill (e.g., Python, React, AWS)"
              />
              <button
                onClick={handleAddSkill}
                className="px-6 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors font-medium"
              >
                Add
              </button>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {cvData.skills.map((skill) => (
                <div
                  key={skill}
                  className="px-4 py-2 bg-teal-50 text-teal-700 rounded-lg flex items-center space-x-2"
                >
                  <span>{skill}</span>
                  <button
                    onClick={() => handleRemoveSkill(skill)}
                    className="text-teal-600 hover:text-teal-800"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={() => setView('landing')}
              className="px-6 py-3 text-slate-700 font-medium hover:bg-slate-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveCV}
              disabled={loading}
              className="px-8 py-3 bg-navy-900 text-white rounded-lg hover:bg-navy-800 transition-colors font-semibold disabled:opacity-50 flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <span>Save CV</span>
              )}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

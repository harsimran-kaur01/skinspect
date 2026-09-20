import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitQuestionnaire, getQuestionnaire } from '../../api/questionnaire'

export default function QuestionnaireForm() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [currentSection, setCurrentSection] = useState(0)
  const [form, setForm] = useState({
    // Section 1 – Basic Profile
    skin_type: '',
    age_group: '',
    biological_sex: '',
    // Section 2 – Skin History & Sensitivity (SAFETY GATE FIRST)
    allergies: [],
    diagnosed_conditions: [],
    under_dermatologist_care: '',
    pregnant: '',
    hormonal_pattern: '',
    shaving_irritation: '',
    // Section 3 – Current Routine
    routine_complexity: '',
    active_ingredients: [],
    sunscreen_use: '',
    // Section 4 – Lifestyle
    sun_exposure: '',
    sleep_quality: '',
    stress_level: '',
    smoking: '',
    // Section 5 – Goals
    primary_concern: '',
    secondary_concern: '',
    budget: 'mid-range',
    routine_complexity_preference: 'moderate',
  })

  // Sections are computed from form state so the safety section can
  // include a sex-specific follow-up question without needing two
  // separate hand-maintained question sets.
  const sections = [
    {
      title: 'Basic Profile',
      fields: ['skin_type', 'age_group', 'biological_sex']
    },
    {
      title: 'Skin History & Safety',
      fields: [
        'pregnant',
        'under_dermatologist_care',
        'allergies',
        'diagnosed_conditions',
        ...(form.biological_sex === 'female' ? ['hormonal_pattern'] : []),
        ...(form.biological_sex === 'male' ? ['shaving_irritation'] : []),
      ]
    },
    {
      title: 'Current Routine',
      fields: ['routine_complexity', 'active_ingredients', 'sunscreen_use']
    },
    {
      title: 'Lifestyle',
      fields: ['sun_exposure', 'sleep_quality', 'stress_level', 'smoking']
    },
    {
      title: 'Your Goals',
      fields: ['primary_concern', 'secondary_concern', 'budget', 'routine_complexity_preference']
    }
  ]

  useEffect(() => {
    getQuestionnaire()
      .then(data => setForm(data.responses))
      .catch(() => {})
  }, [])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    if (type === 'checkbox') {
      const list = form[name] || []
      if (checked) {
        setForm({ ...form, [name]: [...list, value] })
      } else {
        setForm({ ...form, [name]: list.filter(item => item !== value) })
      }
    } else {
      setForm({ ...form, [name]: value })
    }
  }

  const nextSection = () => {
    if (currentSection < sections.length - 1) {
      setCurrentSection(currentSection + 1)
    }
  }

  const prevSection = () => {
    if (currentSection > 0) {
      setCurrentSection(currentSection - 1)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await submitQuestionnaire(form)
      navigate('/transition', {
        state: {
          nextPath: '/scan',
          message: "Great! Now let's take a photo for analysis."
        }
      })
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to save questionnaire')
    } finally {
      setLoading(false)
    }
  }

  const renderField = (fieldName) => {
    switch (fieldName) {
      case 'skin_type':
        return (
          <div>
            <label className="block text-sm font-medium">Skin Type (self‑assessment)</label>
            <select name="skin_type" value={form.skin_type} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="dry">Dry</option>
              <option value="oily">Oily</option>
              <option value="combination">Combination</option>
              <option value="normal">Normal</option>
              <option value="sensitive">Sensitive</option>
            </select>
          </div>
        )
      case 'age_group':
        return (
          <div>
            <label className="block text-sm font-medium">Age Range</label>
            <select name="age_group" value={form.age_group} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="under-18">Under 18</option>
              <option value="18-24">18–24</option>
              <option value="25-34">25–34</option>
              <option value="35-44">35–44</option>
              <option value="45-54">45–54</option>
              <option value="55+">55+</option>
            </select>
          </div>
        )
      case 'biological_sex':
        return (
          <div>
            <label className="block text-sm font-medium">Biological Sex</label>
            <select name="biological_sex" value={form.biological_sex} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
              <option value="prefer-not-to-say">Prefer not to say</option>
            </select>
          </div>
        )
      case 'hormonal_pattern':
        return (
          <div>
            <label className="block text-sm font-medium">Does your acne tend to flare around your cycle (jawline/chin breakouts)?</label>
            <select name="hormonal_pattern" value={form.hormonal_pattern} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="yes">Yes, noticeably</option>
              <option value="somewhat">Somewhat</option>
              <option value="no">No / not sure</option>
            </select>
          </div>
        )
      case 'shaving_irritation':
        return (
          <div>
            <label className="block text-sm font-medium">Do you get irritation or ingrown hairs from shaving?</label>
            <select name="shaving_irritation" value={form.shaving_irritation} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="yes">Yes, regularly</option>
              <option value="occasionally">Occasionally</option>
              <option value="no">No / doesn't apply</option>
            </select>
          </div>
        )
      case 'pregnant':
        return (
          <div className="bg-yellow-50 p-4 rounded border border-yellow-200">
            <label className="block text-sm font-medium text-yellow-800">⚠️ Are you pregnant or breastfeeding?</label>
            <select name="pregnant" value={form.pregnant} onChange={handleChange} className="w-full p-2 border rounded mt-1">
              <option value="">Select...</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
              <option value="prefer-not-to-say">Prefer not to say</option>
            </select>
            <p className="text-xs text-yellow-600 mt-1">This helps us exclude ingredients that may not be safe.</p>
          </div>
        )
      case 'under_dermatologist_care':
        return (
          <div>
            <label className="block text-sm font-medium">Are you currently under dermatologist care?</label>
            <select name="under_dermatologist_care" value={form.under_dermatologist_care} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
        )
      case 'allergies':
        return (
          <div>
            <label className="block text-sm font-medium">Known allergies or reactions (select all that apply)</label>
            <div className="grid grid-cols-2 gap-2 mt-1">
              {['fragrance', 'retinoids', 'salicylic_acid', 'benzoyl_peroxide', 'sulfates', 'none'].map(opt => (
                <label key={opt} className="flex items-center space-x-2 text-sm">
                  <input type="checkbox" name="allergies" value={opt} checked={(form.allergies || []).includes(opt)} onChange={handleChange} />
                  <span>{opt.replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          </div>
        )
      case 'diagnosed_conditions':
        return (
          <div>
            <label className="block text-sm font-medium">Diagnosed skin conditions (select all that apply)</label>
            <div className="grid grid-cols-2 gap-2 mt-1">
              {['eczema', 'rosacea', 'psoriasis', 'melasma', 'acne', 'none', 'prefer-not-to-say'].map(opt => (
                <label key={opt} className="flex items-center space-x-2 text-sm">
                  <input type="checkbox" name="diagnosed_conditions" value={opt} checked={(form.diagnosed_conditions || []).includes(opt)} onChange={handleChange} />
                  <span>{opt.replace(/-/g, ' ').replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          </div>
        )
      case 'routine_complexity':
        return (
          <div>
            <label className="block text-sm font-medium">Current routine complexity</label>
            <select name="routine_complexity" value={form.routine_complexity} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="minimal">Minimal (1‑2 steps)</option>
              <option value="moderate">Moderate (3‑4 steps)</option>
              <option value="extensive">Extensive (5+ steps)</option>
            </select>
          </div>
        )
      case 'active_ingredients':
        return (
          <div>
            <label className="block text-sm font-medium">Active ingredients currently in use</label>
            <div className="grid grid-cols-2 gap-2 mt-1">
              {['retinol', 'vitamin_c', 'salicylic_acid', 'benzoyl_peroxide', 'hyaluronic_acid', 'niacinamide', 'none'].map(opt => (
                <label key={opt} className="flex items-center space-x-2 text-sm">
                  <input type="checkbox" name="active_ingredients" value={opt} checked={(form.active_ingredients || []).includes(opt)} onChange={handleChange} />
                  <span>{opt.replace(/_/g, ' ')}</span>
                </label>
              ))}
            </div>
          </div>
        )
      case 'sunscreen_use':
        return (
          <div>
            <label className="block text-sm font-medium">How often do you use sunscreen?</label>
            <select name="sunscreen_use" value={form.sunscreen_use} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="daily">Daily</option>
              <option value="sometimes">Sometimes</option>
              <option value="never">Never</option>
            </select>
          </div>
        )
      case 'sun_exposure':
        return (
          <div>
            <label className="block text-sm font-medium">Daily sun exposure</label>
            <select name="sun_exposure" value={form.sun_exposure} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="none">Mostly indoors</option>
              <option value="less-than-1hr">Less than 1 hour</option>
              <option value="1-3hr">1–3 hours</option>
              <option value="3hr+">3+ hours</option>
            </select>
          </div>
        )
      case 'sleep_quality':
        return (
          <div>
            <label className="block text-sm font-medium">Sleep quality</label>
            <select name="sleep_quality" value={form.sleep_quality} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="poor">Poor</option>
              <option value="average">Average</option>
              <option value="good">Good</option>
            </select>
          </div>
        )
      case 'stress_level':
        return (
          <div>
            <label className="block text-sm font-medium">Stress level</label>
            <select name="stress_level" value={form.stress_level} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
        )
      case 'smoking':
        return (
          <div>
            <label className="block text-sm font-medium">Do you smoke or vape?</label>
            <select name="smoking" value={form.smoking} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
        )
      case 'primary_concern':
        return (
          <div>
            <label className="block text-sm font-medium">What's your primary skin concern?</label>
            <select name="primary_concern" value={form.primary_concern} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="acne">Clear acne</option>
              <option value="wrinkles">Reduce fine lines & wrinkles</option>
              <option value="hyperpigmentation">Even skin tone</option>
              <option value="general-maintenance">General maintenance</option>
            </select>
          </div>
        )
      case 'secondary_concern':
        return (
          <div>
            <label className="block text-sm font-medium">Secondary concern (optional)</label>
            <select name="secondary_concern" value={form.secondary_concern} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="">Select...</option>
              <option value="acne">Clear acne</option>
              <option value="wrinkles">Reduce fine lines & wrinkles</option>
              <option value="hyperpigmentation">Even skin tone</option>
              <option value="general-maintenance">General maintenance</option>
            </select>
          </div>
        )
      case 'budget':
        return (
          <div>
            <label className="block text-sm font-medium">Preferred price range</label>
            <select name="budget" value={form.budget} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="budget">Budget</option>
              <option value="mid-range">Mid‑range</option>
              <option value="premium">Premium</option>
            </select>
          </div>
        )
      case 'routine_complexity_preference':
        return (
          <div>
            <label className="block text-sm font-medium">Preferred routine complexity</label>
            <select name="routine_complexity_preference" value={form.routine_complexity_preference} onChange={handleChange} className="w-full p-2 border rounded">
              <option value="minimal">Minimal (2 steps)</option>
              <option value="moderate">Moderate (3‑4 steps)</option>
              <option value="extensive">Extensive (5+ steps)</option>
            </select>
          </div>
        )
      default:
        return null
    }
  }

  const currentSectionData = sections[currentSection]

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Skin Assessment</h1>
        <div className="flex gap-2 mt-2">
          {sections.map((_, idx) => (
            <div
              key={idx}
              className={`h-2 flex-1 rounded ${idx <= currentSection ? 'bg-blue-600' : 'bg-gray-300'}`}
            />
          ))}
        </div>
        <p className="text-sm text-gray-500 mt-1">Step {currentSection + 1} of {sections.length}</p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">{currentSectionData.title}</h2>
          <div className="space-y-4">
            {currentSectionData.fields.map(field => (
              <div key={field}>
                {renderField(field)}
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-between mt-6">
          <button
            type="button"
            onClick={prevSection}
            disabled={currentSection === 0}
            className="px-6 py-2 border rounded disabled:opacity-50"
          >
            Back
          </button>
          {currentSection === sections.length - 1 ? (
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Complete & Continue →'}
            </button>
          ) : (
            <button
              type="button"
              onClick={nextSection}
              className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Next →
            </button>
          )}
        </div>
      </form>
    </div>
  )
}

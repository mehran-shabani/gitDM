import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiAiSummariesCreate } from '../../api/generated/gitdmApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Label } from '../../components/ui/Label';
import { Textarea } from '../../components/ui/Textarea';
import { Select } from '../../components/ui/Select';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { useToast } from '../../hooks/useToast';
import type { CreateAISummary, SummaryTypeEnum } from '../../api/generated/gitdmApi.schemas';
import { Link } from 'react-router-dom';

// Constants
const CONTENT_MAX_LENGTH = 10000;
const CONTENT_MIN_LENGTH = 10;

// Type-safe form state interface
interface FormState {
  patient_id: string;
  content: string;
  content_type_model?: string;
  object_id?: string;
  context?: string;
  summary_type: SummaryTypeEnum;
  topic_hint?: string;
  async_processing: boolean;
  errors: Record<string, string>;
}

export function CreateAISummary() {
  const navigate = useNavigate();
  const { addToast } = useToast();
  const createMutation = useApiAiSummariesCreate();

  const [formData, setFormData] = useState<FormState>({
    patient_id: '',
    content: '',
    content_type_model: '',
    object_id: '',
    context: '',
    summary_type: 'medical_record' as SummaryTypeEnum,
    topic_hint: '',
    async_processing: false,
    errors: {},
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrors({});

    // Enhanced validation
    const newErrors: Record<string, string> = {};
    
    // Validate patient_id as positive integer
    if (!formData.patient_id) {
      newErrors.patient_id = 'Patient ID is required';
    } else {
      const patientId = parseInt(formData.patient_id, 10);
      if (isNaN(patientId) || patientId <= 0) {
        newErrors.patient_id = 'Patient ID must be a positive integer';
      }
    }
    
    // Validate content
    const trimmedContent = formData.content.trim();
    if (!trimmedContent) {
      newErrors.content = 'Content is required';
    } else if (trimmedContent.length < CONTENT_MIN_LENGTH) {
      newErrors.content = `Content must be at least ${CONTENT_MIN_LENGTH} characters`;
    } else if (trimmedContent.length > CONTENT_MAX_LENGTH) {
      newErrors.content = `Content must not exceed ${CONTENT_MAX_LENGTH.toLocaleString()} characters`;
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      // Build payload with only non-empty fields
      const payload: Partial<CreateAISummary> = {
        patient_id: parseInt(formData.patient_id, 10),
        content: trimmedContent,
        summary_type: formData.summary_type,
        async_processing: formData.async_processing,
      };
      
      // Only include optional fields if they have values
      if (formData.content_type_model?.trim()) {
        payload.content_type_model = formData.content_type_model.trim();
      }
      if (formData.object_id?.trim()) {
        payload.object_id = formData.object_id.trim();
      }
      if (formData.context?.trim()) {
        payload.context = formData.context.trim();
      }
      if (formData.topic_hint?.trim()) {
        payload.topic_hint = formData.topic_hint.trim();
      }
      await createMutation.mutateAsync({ data: payload as CreateAISummary });

      addToast('success', 'AI Summary Created', 'The AI summary has been created successfully.');
      navigate('/ai-summaries');
    } catch (error: any) {
      // Enhanced error handling
      const errorMessage = error?.response?.data?.detail || 
                          error?.response?.data?.message || 
                          error?.message || 
                          'An unexpected error occurred';
      addToast('error', 'Failed to create AI summary', errorMessage);
      console.error('Failed to create AI summary:', error);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  // Get error message for display
  const getErrorMessage = (): string => {
    if (!createMutation.error) return '';
    const error = createMutation.error as any;
    return error?.response?.data?.detail || 
           error?.response?.data?.message || 
           error?.message || 
           'An unexpected error occurred';
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-6">
        <Link
          to="/ai-summaries"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to AI Summaries
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create AI Summary</CardTitle>
          <CardDescription>
            Generate a new AI summary for medical content
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="patient_id">Patient ID *</Label>
              <Input
                id="patient_id"
                name="patient_id"
                type="number"
                value={formData.patient_id}
                onChange={handleChange}
                placeholder="Enter patient ID"
                min={1}
                step={1}
                required
                inputMode="numeric"
                pattern="[0-9]*"
                aria-required="true"
                aria-invalid={!!errors.patient_id}
                aria-describedby={errors.patient_id ? "patient-id-error" : undefined}
              />
              {errors.patient_id && (
                <p id="patient-id-error" className="text-sm text-red-500">{errors.patient_id}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="content">Content to Summarize *</Label>
              <Textarea
                id="content"
                name="content"
                value={formData.content}
                onChange={handleChange}
                placeholder="Enter the medical content to be summarized..."
                rows={6}
                minLength={CONTENT_MIN_LENGTH}
                maxLength={CONTENT_MAX_LENGTH}
                required
                aria-invalid={!!errors.content}
                aria-describedby={errors.content ? 'content-error' : undefined}
              />
              {errors.content && (
                <p id="content-error" className="text-sm text-red-500">{errors.content}</p>
              )}
              <p className="text-sm text-gray-500">
                {formData.content.length}/{CONTENT_MAX_LENGTH.toLocaleString()} characters
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="summary_type">Summary Type</Label>
              <Select
                id="summary_type"
                name="summary_type"
                value={formData.summary_type}
                onChange={handleChange}
              >
                <option value="medical_record">Medical Record</option>
                <option value="encounter">Patient Encounter</option>
                <option value="lab_results">Laboratory Results</option>
                <option value="medications">Medications</option>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="context">Additional Context</Label>
              <Textarea
                id="context"
                name="context"
                value={formData.context}
                onChange={handleChange}
                placeholder="Optional patient context for better summarization..."
                rows={3}
                maxLength={2000}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="topic_hint">Topic Hint</Label>
              <Input
                id="topic_hint"
                name="topic_hint"
                value={formData.topic_hint}
                onChange={handleChange}
                placeholder="e.g., diabetes, hypertension"
                maxLength={200}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Input
                type="checkbox"
                id="async_processing"
                name="async_processing"
                checked={formData.async_processing}
                onChange={handleChange}
                className="h-4 w-4 rounded border-gray-300"
                aria-invalid={!!errors.async_processing}
                aria-describedby={errors.async_processing ? 'async-processing-error' : undefined}
              />
              <Label htmlFor="async_processing">
                Process asynchronously (recommended for large content)
              </Label>
            </div>

            {createMutation.error && (
              <ErrorMessage
                title="Submission Error"
                message={getErrorMessage()}
              />
            )}

            <div className="flex justify-end gap-3">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/ai-summaries')}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Create Summary
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
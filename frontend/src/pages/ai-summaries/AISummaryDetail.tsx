import { useParams, useNavigate, Link } from 'react-router-dom';
import { useApiAiSummariesRetrieve, useApiAiSummariesDestroy } from '../../api/generated/gitdmApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Loading } from '../../components/ui/Loading';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { ArrowLeft, Edit, Trash2, RefreshCw, FileText, User, Calendar, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';
import { useToast } from '../../hooks/useToast';
import { getErrorMessage } from '../../lib/utils';

export function AISummaryDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { addToast } = useToast();

  const { data, isLoading, error, refetch } = useApiAiSummariesRetrieve(
    parseInt(id!, 10),
    { query: { enabled: !!id } }
  );

  const deleteMutation = useApiAiSummariesDestroy();

  const handleDelete = async () => {
    if (!id) return;
    
    if (window.confirm('Are you sure you want to delete this AI summary?')) {
      try {
        await deleteMutation.mutateAsync({ id: parseInt(id, 10) });
        addToast('success', 'AI Summary Deleted', 'The AI summary has been deleted successfully.');
        navigate('/ai-summaries');
      } catch (error) {
        addToast('error', 'Failed to delete AI summary', 'Please try again later.');
        console.error('Failed to delete AI summary:', error);
      }
    }
  };

  if (isLoading) {
    return <Loading className="mt-8" size="lg" />;
  }

  if (error || !data) {
    return (
      <ErrorMessage
        title="Failed to load AI summary"
        message={getErrorMessage(error, 'AI summary not found')}
        className="mt-8"
      />
    );
  }

  const summary = data;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link
          to="/ai-summaries"
          className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to AI Summaries
        </Link>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Link to={`/ai-summaries/${id}/edit`}>
            <Button variant="outline" size="sm">
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </Link>
          <Button
            variant="destructive"
            size="sm"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-gray-500" />
                AI Summary #{summary.id}
              </CardTitle>
              <CardDescription>
                Generated summary for {summary.resource_type || 'medical content'}
              </CardDescription>
            </div>
            <Badge variant="secondary">{summary.resource_type || 'Unknown'}</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-sm text-gray-500">Patient</p>
                <Link
                  to={`/patients/${summary.patient}`}
                  className="text-sm font-medium text-blue-600 hover:underline"
                >
                  Patient #{summary.patient}
                </Link>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p className="text-sm font-medium">
                  {summary.created_at
                    ? format(new Date(summary.created_at), 'MMM dd, yyyy h:mm a')
                    : '-'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <div>
                <p className="text-sm text-gray-500">Updated</p>
                <p className="text-sm font-medium">
                  {summary.updated_at
                    ? format(new Date(summary.updated_at), 'MMM dd, yyyy h:mm a')
                    : '-'}
                </p>
              </div>
            </div>
          </div>

          {/* Summary Content */}
          <div>
            <h3 className="text-lg font-semibold mb-3">Summary</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-gray-700 whitespace-pre-wrap">{summary.summary}</p>
            </div>
          </div>

          {/* References */}
          {summary.references && summary.references.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3">
                References ({summary.references.length})
              </h3>
              <div className="space-y-2">
                {summary.references.map((reference, index) => (
                  <div
                    key={`${index}-${reference}`}
                    className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg"
                  >
                    <ExternalLink className="h-4 w-4 text-gray-400 mt-0.5" />
                    <p className="text-sm text-gray-700">{reference}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Related Resource Info */}
          {(summary.content_type || summary.object_id) && (
            <div className="border-t pt-4">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Related Resource</h3>
              <div className="flex gap-4 text-sm">
                {summary.content_type && (
                  <div>
                    <span className="text-gray-500">Content Type:</span>{' '}
                    <span className="font-medium">{summary.content_type}</span>
                  </div>
                )}
                {summary.object_id && (
                  <div>
                    <span className="text-gray-500">Object ID:</span>{' '}
                    <span className="font-medium">{summary.object_id}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

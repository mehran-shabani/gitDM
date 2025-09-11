import { useApiAiSummariesList } from '../../api/generated/gitdmApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { Eye, RefreshCw, Plus, Loader2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';
import { getErrorMessage } from '../../lib/utils';

export function AISummariesList() {
  const { data, isLoading, error, refetch, isFetching } = useApiAiSummariesList();

  if (isLoading) {
    return <Loading className="mt-8" size="lg" />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load AI summaries"
        message={getErrorMessage(error, 'An unexpected error occurred')}
        className="mt-8"
      />
    );
  }

    const summaries = data || [];

  // Safe date formatting with fallback
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '-';
    
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return '-';
      
      return formatDistanceToNow(date, { addSuffix: true });
    } catch {
      return '-';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>AI Summaries</CardTitle>
              <CardDescription>
                AI-generated medical summaries for patient records
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
                disabled={isFetching}
              >
                {isFetching ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Refreshing...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </>
                )}
              </Button>
              <Link to="/ai-summaries/new">
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Summary
                </Button>
              </Link>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {summaries.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No AI summaries found. Create your first summary to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Patient ID</TableHead>
                  <TableHead>Resource Type</TableHead>
                  <TableHead>Summary Preview</TableHead>
                  <TableHead>References</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summaries.map((summary) => (
                  <TableRow key={summary.id}>
                    <TableCell className="font-medium">{summary.id}</TableCell>
                    <TableCell>
                      <Link
                        to={`/patients/${summary.patient}`}
                        className="text-blue-600 hover:underline"
                      >
                        {summary.patient}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {summary.resource_type || 'Unknown'}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">
                      {summary.summary_preview}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {summary.references_count} refs
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {formatDate(summary.created_at)}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {formatDate(summary.updated_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link to={`/ai-summaries/${summary.id}`}>
                        <Button 
                          variant="ghost" 
                          size="sm"
                          aria-label={`View summary ${summary.id}`}
                        >
                          <Eye className="h-4 w-4" />
                          <span className="sr-only">View summary</span>
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
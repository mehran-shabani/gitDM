import { useApiRefsList } from '../../api/generated/gitdmApi';
import type { ClinicalReference } from '../../api/generated/gitdmApi.schemas';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { Eye, RefreshCw, Plus, BookOpen, ExternalLink, Calendar } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { AxiosError } from 'axios';

export function ClinicalReferencesList() {
  const { data, isLoading, error, refetch } = useApiRefsList();

  if (isLoading) {
    return <Loading className="mt-8" size="lg" />;
  }

  if (error) {
    // Enhanced error handling
    const errorMessage = (error as AxiosError<{ detail?: string; message?: string }>)?.response?.data?.detail || 
                        (error as AxiosError<{ detail?: string; message?: string }>)?.response?.data?.message || 
                        (error as AxiosError<{ detail?: string; message?: string }>)?.message || 
                        'An unexpected error occurred';
    return (
      <ErrorMessage
        title="Failed to load clinical references"
        message={errorMessage}
        className="mt-8"
      />
    );
  }

  const references = data || [];

  // Improved year validation with type safety
  const getYearBadgeVariant = (year: number | string | null | undefined): 'default' | 'secondary' | 'outline' => {
    // Validate and coerce input
    const yearNum = typeof year === 'number' ? year : parseInt(String(year), 10);
    
    // Check if valid year
    if (!isFinite(yearNum) || yearNum < 1900 || yearNum > new Date().getFullYear() + 1) {
      return 'outline'; // Invalid or future year
    }
    
    const currentYear = new Date().getFullYear();
    const age = Math.max(0, currentYear - yearNum); // Clamp negative ages to 0
    
    if (age <= 2) return 'default'; // Recent
    if (age <= 5) return 'secondary'; // Fairly recent
    return 'outline'; // Older
  };

  // Safe title truncation with fallback
  const truncateTitle = (title: string | null | undefined, maxLength = 60) => {
    const safeTitle = title || 'Untitled Reference';
    return safeTitle.length > maxLength ? safeTitle.substring(0, maxLength) + '...' : safeTitle;
  };

  // Get display title with fallback
  const getDisplayTitle = (reference: ClinicalReference) => {
    return reference.title || `Reference ${reference.id}`;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Clinical References</CardTitle>
              <CardDescription>
                Access medical literature and clinical guidelines
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => refetch()}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Link to="/clinical-references/new">
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Reference
                </Button>
              </Link>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {references.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No clinical references found. Add your first reference to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Title</TableHead>
                  <TableHead>Source</TableHead>
                  <TableHead>Year</TableHead>
                  <TableHead>Topic</TableHead>
                  <TableHead>URL</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {references.map((reference: ClinicalReference) => {
                  const displayTitle = getDisplayTitle(reference);
                  return (
                    <TableRow key={reference.id}>
                      <TableCell className="font-medium">{reference.id}</TableCell>
                      <TableCell>
                        <div className="flex items-start gap-2 max-w-md">
                          <BookOpen className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                          <span className="font-medium" title={displayTitle}>
                            {truncateTitle(displayTitle)}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{reference.source}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge 
                          variant={getYearBadgeVariant(reference.year)}
                          className="flex items-center gap-1 w-fit"
                        >
                          <Calendar className="h-3 w-3" />
                          {reference.year || 'Unknown'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{reference.topic}</Badge>
                      </TableCell>
                      <TableCell>
                        {reference.url ? (
                          <a
                            href={reference.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-blue-600 hover:underline"
                          >
                            <ExternalLink className="h-3 w-3" />
                            View
                          </a>
                        ) : (
                          <span className="text-gray-400">No URL</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link to={`/clinical-references/${reference.id}`}>
                          <Button 
                            variant="ghost" 
                            size="sm"
                            aria-label={`View reference ${displayTitle}`}
                            title={`View reference ${displayTitle}`}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
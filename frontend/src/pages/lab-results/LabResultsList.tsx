import { useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { Eye, RefreshCw, Plus, FlaskConical, TrendingUp, TrendingDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { useApiLabsList } from '../../api/generated/gitdmApi';
import { getErrorMessage } from '../../lib/utils';
import type { LabResult } from '../../api/generated/gitdmApi.schemas';


// Helper function moved outside component for better performance
const getValueStatus = (value: string): 'normal' | 'low' | 'high' => {
  const numValue = parseFloat(value);
  if (isNaN(numValue)) return 'normal';
  // This is a simplified example - in real app, you'd compare against reference ranges
  if (numValue < 0) return 'low';
  if (numValue > 100) return 'high';
  return 'normal';
};

export function LabResultsList() {
  const { data, isLoading, error, refetch } = useApiLabsList();

  // Memoized function to prevent recreation on each render
  const getStatusBadge = useCallback((status: string) => {
    switch (status) {
      case 'high':
        return (
          <Badge variant="destructive" className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            High
          </Badge>
        );
      case 'low':
        return (
          <Badge variant="secondary" className="flex items-center gap-1">
            <TrendingDown className="h-3 w-3" />
            Low
          </Badge>
        );
      default:
        return <Badge variant="outline">Normal</Badge>;
    }
  }, []);

  if (isLoading) {
    return <Loading className="mt-8" size="lg" />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load lab results"
        message={getErrorMessage(error, 'Failed to load lab results')}
        className="mt-8"
      />
    );
  }

  const results = data || [];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Lab Results</CardTitle>
              <CardDescription>
                Track and review laboratory test results
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
              <Link to="/lab-results/new">
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  Add Result
                </Button>
              </Link>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {results.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No lab results found. Add your first lab result to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Encounter</TableHead>
                  <TableHead>LOINC Code</TableHead>
                  <TableHead>Value</TableHead>
                  <TableHead>Unit</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Taken At</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {results.map((result: LabResult) => (
                  <TableRow key={result.id}>
                    <TableCell className="font-medium">{result.id}</TableCell>
                    <TableCell>
                      <Link
                        to={`/patients/${result.patient}`}
                        className="text-blue-600 hover:underline"
                      >
                        Patient #{result.patient}
                      </Link>
                    </TableCell>
                    <TableCell>
                      {result.encounter ? (
                        <Link
                          to={`/encounters/${result.encounter}`}
                          className="text-blue-600 hover:underline"
                        >
                          Encounter #{result.encounter}
                        </Link>
                      ) : (
                        <span className="text-gray-400">No encounter</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <FlaskConical className="h-4 w-4 text-gray-400" />
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                          {result.loinc}
                        </code>
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">{result.value}</TableCell>
                    <TableCell>{result.unit}</TableCell>
                    <TableCell>{getStatusBadge(getValueStatus(result.value))}</TableCell>
                    <TableCell>
                      <div>
                        <div className="font-medium">
                          {format(parseISO(result.taken_at), 'MMM dd, yyyy')}
                        </div>
                        <div className="text-sm text-gray-500">
                          {formatDistanceToNow(parseISO(result.taken_at), {
                            addSuffix: true,
                          })}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <Link to={`/lab-results/${result.id}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
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
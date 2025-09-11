import { useApiEncountersList } from '../../api/generated/gitdmApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { Eye, RefreshCw, Plus, Calendar, FileText } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getErrorMessage } from '../../lib/utils';
import { format, formatDistanceToNow, parseISO } from 'date-fns';
import type { Encounter } from '../../api/generated/gitdmApi.schemas';


export function EncountersList() {
  const { data, isLoading, error, refetch } = useApiEncountersList();

  if (isLoading) {
    return <Loading className="mt-8" size="lg" />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load encounters"
        message={getErrorMessage(error, 'Unknown error')}
        className="mt-8"
      />
    );
  }

  const encounters = data || [];

  const truncateText = (text?: string, maxLength = 100) => {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Patient Encounters</CardTitle>
              <CardDescription>
                View and manage patient encounters and visits
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
              <Link to="/encounters/new">
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Encounter
                </Button>
              </Link>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {encounters.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No encounters found. Create your first encounter to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Date & Time</TableHead>
                  <TableHead>Subjective</TableHead>
                  <TableHead>SOAP Status</TableHead>
                  <TableHead>Created By</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {encounters.map((encounter: Encounter) => (
                  <TableRow key={encounter.id}>
                    <TableCell className="font-medium">{encounter.id}</TableCell>
                    <TableCell>
                      <Link
                        to={`/patients/${encounter.patient}`}
                        className="text-blue-600 hover:underline"
                      >
                        Patient #{encounter.patient}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <div>
                          <div className="font-medium">
                            {format(parseISO(encounter.occurred_at), 'MMM dd, yyyy')}
                          </div>
                          <div className="text-sm text-gray-500">
                            {format(parseISO(encounter.occurred_at), 'h:mm a')}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-xs">
                      {encounter.subjective ? (
                        <div className="flex items-start gap-2">
                          <FileText className="h-4 w-4 text-gray-400 mt-0.5" />
                          <span className="text-sm">
                            {truncateText(encounter.subjective)}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">No subjective notes</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Badge variant={encounter.subjective ? 'default' : 'outline'}>S</Badge>
                        <Badge variant={encounter.objective ? 'default' : 'outline'}>O</Badge>
                        <Badge variant={encounter.assessment ? 'default' : 'outline'}>A</Badge>
                        <Badge variant={encounter.plan ? 'default' : 'outline'}>P</Badge>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Link
                        to={`/users/${encounter.created_by}`}
                        className="text-blue-600 hover:underline"
                      >
                        User #{encounter.created_by}
                      </Link>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {encounter.occurred_at ? (
                        formatDistanceToNow(parseISO(encounter.occurred_at), {
                          addSuffix: true,
                        })
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link to={`/encounters/${encounter.id}`}>
                        <Button variant="ghost" size="sm" aria-label={`View encounter ${encounter.id}`} type="button">
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
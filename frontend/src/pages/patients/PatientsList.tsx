import { useApiPatientsList } from '../../api/generated/gitdmApi';
import { SexEnum } from '../../api/generated/gitdmApi';
import type { Patient } from '../../api/generated/gitdmApi.schemas';
import { getErrorMessage } from '../../lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { Eye, RefreshCw, Plus, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import { format, parseISO } from 'date-fns';

export function PatientsList() {
  const { data, isLoading, error, refetch } = useApiPatientsList();

  if (isLoading) {
    return <Loading className="mt-8" size="lg" />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load patients"
        message={getErrorMessage(error, 'Unexpected error')}
        className="mt-8"
      />
    );
  }

  const patients = data || [];

  // Typed lookup map for sex badge variants
  const sexBadgeVariants: Record<SexEnum, 'default' | 'secondary' | 'outline'> = {
    [SexEnum.MALE]: 'default',
    [SexEnum.FEMALE]: 'secondary',
    [SexEnum.OTHER]: 'outline',
  } as const;

  const getSexBadgeVariant = (sex?: string | null): 'default' | 'secondary' | 'outline' => {
    return sex && sex in sexBadgeVariants 
      ? sexBadgeVariants[sex as SexEnum]
      : 'outline';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Patients</CardTitle>
              <CardDescription>
                Manage patient records and information
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
              <Link to="/patients/new">
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Patient
                </Button>
              </Link>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {patients.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No patients found. Add your first patient to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>National ID</TableHead>
                  <TableHead>Full Name</TableHead>
                  <TableHead>Date of Birth</TableHead>
                  <TableHead>Sex</TableHead>
                  <TableHead>Primary Doctor</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.map((patient: Patient) => (
                  <TableRow key={patient.id}>
                    <TableCell className="font-medium">{patient.id}</TableCell>
                    <TableCell>
                      {patient.national_id || (
                        <span className="text-gray-400">Not set</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-gray-400" />
                        {patient.full_name || 'Unknown'}
                      </div>
                    </TableCell>
                    <TableCell>
                      {patient.dob ? (
                        format(parseISO(patient.dob), 'MMM dd, yyyy')
                      ) : (
                        <span className="text-gray-400">Not set</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={getSexBadgeVariant(patient.sex)}>
                        {patient.sex || 'Unknown'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {patient.primary_doctor_id ? (
                        <Link
                          to={`/doctors/${patient.primary_doctor_id}`}
                          className="text-blue-600 hover:underline"
                        >
                          Doctor #{patient.primary_doctor_id}
                        </Link>
                      ) : (
                        <span className="text-gray-400">Not assigned</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {patient?.created_at
                        ? format(parseISO(patient.created_at), 'MMM dd, yyyy')
                        : <span className="text-gray-400">Not set</span>}
                    </TableCell>
                    <TableCell className="text-right">
                      <Link to={`/patients/${patient.id}`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          aria-label={`View patient ${patient.id}`}
                          type="button"
                        >
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
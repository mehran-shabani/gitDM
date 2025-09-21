import { useApiMedsList } from '../../api/generated/gitdmApi';
import { getErrorMessage } from '../../lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { Loading } from '../../components/ui/Loading';
import { ErrorMessage } from '../../components/ui/ErrorMessage';
import { Eye, RefreshCw, Plus, Pill, Clock, CheckCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { format, isBefore, isAfter, parseISO } from 'date-fns';
import type { MedicationOrder } from '../../api/generated/gitdmApi.schemas';
import type { MedicationOrderFrequencyEnum } from '../../api/generated/gitdmApi';

type MedicationStatus = {
  status: 'scheduled' | 'active' | 'completed';
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  variant: 'secondary' | 'default' | 'outline';
};

export function MedicationsList() {
  const { data, isLoading, error, refetch } = useApiMedsList();

  if (isLoading) {
    return <Loading className="mt-8" size="lg" />;
  }

  if (error) {
    return (
      <ErrorMessage
        title="Failed to load medications"
        message={getErrorMessage(error, 'Unknown error')}
        className="mt-8"
      />
    );
  }

  const medications = data || [];

  const getFrequencyLabel = (frequency?: MedicationOrderFrequencyEnum) => {
    const labels: Record<MedicationOrderFrequencyEnum, string> = {
      QD: 'Once daily',
      BID: 'Twice daily',
      TID: 'Three times daily',
      QID: 'Four times daily',
      Q6H: 'Every 6 hours',
      Q8H: 'Every 8 hours',
      Q12H: 'Every 12 hours',
      PRN: 'As needed',
      QW: 'Weekly',
      QM: 'Monthly',
    };
    return frequency ? labels[frequency] : 'Not specified';
  };

  const getMedicationStatus = (startDate: string, endDate?: string | null): MedicationStatus => {
    const now = new Date();
    const start = parseISO(startDate);
    const end = endDate ? parseISO(endDate) : null;

    if (isBefore(now, start)) {
      return { status: 'scheduled', label: 'Scheduled', icon: Clock, variant: 'secondary' as const };
    }
    if (end && isAfter(now, end)) {
      return { status: 'completed', label: 'Completed', icon: CheckCircle, variant: 'outline' as const };
    }
    // Active state (started and not ended, or within date range)
    return { status: 'active', label: 'Active', icon: CheckCircle, variant: 'default' as const };
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Medication Orders</CardTitle>
              <CardDescription>
                Manage medication orders and prescriptions
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
              <Link to="/medications/new">
                <Button size="sm">
                  <Plus className="h-4 w-4 mr-2" />
                  New Order
                </Button>
              </Link>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {medications.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              No medication orders found. Create your first medication order to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Medication</TableHead>
                  <TableHead>ATC Code</TableHead>
                  <TableHead>Dose</TableHead>
                  <TableHead>Frequency</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {medications.map((medication: MedicationOrder) => {
                  const status = getMedicationStatus(medication.start_date, medication.end_date);
                  return (
                    <TableRow key={medication.id}>
                      <TableCell className="font-medium">{medication.id}</TableCell>
                      <TableCell>
                        <Link
                          to={`/patients/${medication.patient}`}
                          className="text-blue-600 hover:underline"
                        >
                          Patient #{medication.patient}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Pill className="h-4 w-4 text-gray-400" />
                          <span className="font-medium">{medication.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                          {medication.atc}
                        </code>
                      </TableCell>
                      <TableCell>{medication.dose}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {getFrequencyLabel(medication.frequency)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <div>{format(parseISO(medication.start_date), 'MMM dd, yyyy')}</div>
                          {medication.end_date && (
                            <>
                              <div className="text-gray-500">to</div>
                              <div>{format(parseISO(medication.end_date), 'MMM dd, yyyy')}</div>
                            </>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={status.variant} className="flex items-center gap-1 w-fit">
                          <status.icon className="h-3 w-3" />
                          {status.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link to={`/medications/${medication.id}`}>
                          <Button variant="ghost" size="sm">
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
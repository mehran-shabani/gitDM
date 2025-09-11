import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FileText, Users, Calendar, FlaskConical, Pill, BookOpen, ArrowRight, Activity } from 'lucide-react';

const features = [
  {
    title: 'AI Summaries',
    description: 'AI-generated medical summaries for patient records',
    icon: FileText,
    href: '/ai-summaries',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
  },
  {
    title: 'Patients',
    description: 'Manage patient records and information',
    icon: Users,
    href: '/patients',
    color: 'text-green-600',
    bgColor: 'bg-green-50',
  },
  {
    title: 'Encounters',
    description: 'View and manage patient encounters',
    icon: Calendar,
    href: '/encounters',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
  },
  {
    title: 'Lab Results',
    description: 'Track and review laboratory test results',
    icon: FlaskConical,
    href: '/lab-results',
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
  },
  {
    title: 'Medications',
    description: 'Manage medication orders and prescriptions',
    icon: Pill,
    href: '/medications',
    color: 'text-pink-600',
    bgColor: 'bg-pink-50',
  },
  {
    title: 'Clinical References',
    description: 'Access medical literature and references',
    icon: BookOpen,
    href: '/clinical-references',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
  },
];

export function Dashboard() {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-8 text-white">
        <div className="flex items-center gap-4 mb-4">
          <Activity className="h-12 w-12" />
          <h1 className="text-3xl font-bold">Welcome to GITDM Client</h1>
        </div>
        <p className="text-blue-100 text-lg mb-6">
          A modern healthcare management system powered by AI for better patient care.
        </p>
        <div className="flex gap-4">
          <Link to="/ai-summaries/new" aria-label="Create AI Summary">
            <Button variant="secondary" size="lg">
              Create AI Summary
            </Button>
          </Link>
          <Link to="/patients/new" aria-label="Add New Patient">
            <Button variant="outline" size="lg" className="text-white border-white hover:bg-white hover:text-purple-600">
              Add New Patient
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Total Patients</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-gray-500">Active records</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">AI Summaries</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-gray-500">Generated this month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Encounters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-gray-500">This week</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">Lab Results</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">--</div>
            <p className="text-xs text-gray-500">Pending review</p>
          </CardContent>
        </Card>
      </div>

      {/* Features Grid */}
      <div>
        <h2 className="text-2xl font-bold mb-6">Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => (
            <Link key={feature.href} to={feature.href} aria-label={`Open ${feature.title}`}>
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer">
                <CardHeader>
                  <div className={`inline-flex p-3 rounded-lg ${feature.bgColor} mb-4`}>
                    <feature.icon className={`h-6 w-6 ${feature.color}`} />
                  </div>
                  <CardTitle className="flex items-center justify-between">
                    {feature.title}
                    <ArrowRight className="h-5 w-5 text-gray-400" />
                  </CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
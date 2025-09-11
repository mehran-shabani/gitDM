// Central query keys management for React Query
// This ensures consistent cache invalidation and query management

// JSON-serializable types for filters
type JsonPrimitive = string | number | boolean | null;
type JsonObject = { [key: string]: JsonValue };
type JsonArray = JsonValue[];
type JsonValue = JsonPrimitive | JsonObject | JsonArray;

// Stable stringify for filters
function stableStringify(obj: JsonValue): string {
  if (obj === null || typeof obj !== 'object') {
    return JSON.stringify(obj);
  }
  if (Array.isArray(obj)) {
    return JSON.stringify(obj);
  }
  // Sort object keys for stable serialization
  const sortedObj: Record<string, JsonValue> = {};
  Object.keys(obj).sort().forEach(key => {
    sortedObj[key] = obj[key];
  });
  return JSON.stringify(sortedObj);
}

export const queryKeys = {
  all: ['gitdm'] as const,
  
  // AI Summaries
  aiSummaries: {
    all: ['gitdm', 'ai-summaries'] as const,
    lists: () => [...queryKeys.aiSummaries.all, 'list'] as const,
    list: (filters?: JsonObject) => [...queryKeys.aiSummaries.lists(), filters ? stableStringify(filters) : undefined] as const,
    details: () => [...queryKeys.aiSummaries.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.aiSummaries.details(), id] as const,
  },
  
  // Patients
  patients: {
    all: ['gitdm', 'patients'] as const,
    lists: () => [...queryKeys.patients.all, 'list'] as const,
    list: (filters?: JsonObject) => [...queryKeys.patients.lists(), filters ? stableStringify(filters) : undefined] as const,
    details: () => [...queryKeys.patients.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.patients.details(), id] as const,
  },
  
  // Encounters
  encounters: {
    all: ['gitdm', 'encounters'] as const,
    lists: () => [...queryKeys.encounters.all, 'list'] as const,
    list: (filters?: JsonObject) => [...queryKeys.encounters.lists(), filters ? stableStringify(filters) : undefined] as const,
    details: () => [...queryKeys.encounters.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.encounters.details(), id] as const,
  },
  
  // Clinical References
  clinicalReferences: {
    all: ['gitdm', 'clinical-references'] as const,
    lists: () => [...queryKeys.clinicalReferences.all, 'list'] as const,
    list: (filters?: JsonObject) => [...queryKeys.clinicalReferences.lists(), filters ? stableStringify(filters) : undefined] as const,
    details: () => [...queryKeys.clinicalReferences.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.clinicalReferences.details(), id] as const,
  },
  
  // Lab Results
  labResults: {
    all: ['gitdm', 'lab-results'] as const,
    lists: () => [...queryKeys.labResults.all, 'list'] as const,
    list: (filters?: JsonObject) => [...queryKeys.labResults.lists(), filters ? stableStringify(filters) : undefined] as const,
    details: () => [...queryKeys.labResults.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.labResults.details(), id] as const,
  },
  
  // Medication Orders
  medicationOrders: {
    all: ['gitdm', 'medication-orders'] as const,
    lists: () => [...queryKeys.medicationOrders.all, 'list'] as const,
    list: (filters?: JsonObject) => [...queryKeys.medicationOrders.lists(), filters ? stableStringify(filters) : undefined] as const,
    details: () => [...queryKeys.medicationOrders.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.medicationOrders.details(), id] as const,
  },
  
  // Authentication
  auth: {
    all: ['gitdm', 'auth'] as const,
    user: () => [...queryKeys.auth.all, 'user'] as const,
    token: () => [...queryKeys.auth.all, 'token'] as const,
  },
  
  // Versions (for resource history)
  versions: {
    all: ['gitdm', 'versions'] as const,
    // Add lists/details methods for consistency
    lists: (resourceType: string, resourceId: string) => 
      [...queryKeys.versions.all, resourceType, resourceId] as const,
    details: (resourceType: string, resourceId: string) => 
      [...queryKeys.versions.all, resourceType, resourceId] as const,
    // Keep list as backward-compatible alias
    list: (resourceType: string, resourceId: string) => 
      queryKeys.versions.lists(resourceType, resourceId),
  }
};

// Define resource key type
type ResourceKey = Exclude<keyof typeof queryKeys, 'all'>;

// Helper function to invalidate all queries for a specific resource
export const invalidateResourceQueries = (
  queryClient: import('@tanstack/react-query').QueryClient,
  resource: ResourceKey | 'all'
) => {
  if (resource === 'all') {
    // Invalidate all resources
    const allResources: ResourceKey[] = [
      'aiSummaries',
      'patients', 
      'encounters',
      'clinicalReferences',
      'labResults',
      'medicationOrders',
      'auth',
      'versions'
    ];
    
    return Promise.all(
      allResources.map(res => {
        const resourceKeys = queryKeys[res];
        if ('all' in resourceKeys) {
          return queryClient.invalidateQueries({ queryKey: resourceKeys.all });
        }
        return Promise.resolve();
      })
    );
  }
  
  const resourceKeys = queryKeys[resource];
  if ('all' in resourceKeys) {
    return queryClient.invalidateQueries({ queryKey: resourceKeys.all });
  }
};
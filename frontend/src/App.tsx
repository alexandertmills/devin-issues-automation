import { useState, useEffect } from 'react'
import { Github, Play, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import './App.css'

interface GitHubIssue {
  id: number
  github_issue_id: number
  number: number
  html_url: string
  title: string
  body: string
  state: string
  repository: string
  created_at: string
  updated_at: string
}

interface DevinSession {
  session_id: string | null
  status: string | null
  confidence_score: number | null
  action_plan: string | null
  created_at: string | null
}

interface DashboardItem {
  issue: GitHubIssue
  scope_session: DevinSession | null
  execution_session: DevinSession | null
}

interface Repository {
  name: string
  full_name: string
  owner: string
  private: boolean
  description: string
}

function App() {
  const [issues, setIssues] = useState<DashboardItem[]>([])
  const [loading, setLoading] = useState(false)
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [selectedRepository, setSelectedRepository] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [installationId, setInstallationId] = useState('')
  const [verificationStatus, setVerificationStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [verificationMessage, setVerificationMessage] = useState('')
  const [verifiedUsername, setVerifiedUsername] = useState('')
  const [scopingIssues, setScopingIssues] = useState<Set<number>>(new Set())

  const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'


  const fetchRepositories = async () => {
    try {
      const response = await fetch(`${API_BASE}/app/repositories`)
      if (!response.ok) {
        throw new Error(`Failed to fetch repositories: ${response.statusText}`)
      }
      const data = await response.json()
      setRepositories(data.repositories || [])
    } catch (err) {
      console.error('Error fetching repositories:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch repositories')
    }
  }

  const fetchIssues = async () => {
    if (!selectedRepository) {
      setError('Please select a repository first')
      return
    }
    
    const [owner, repo] = selectedRepository.split('/')
    setLoading(true)
    setError(null)
    try {
      const url = `${API_BASE}/issues/${owner}/${repo}?state=all&limit=10`
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      
      const response = await fetch(url, { headers })
      if (!response.ok) {
        throw new Error(`Failed to fetch issues: ${response.statusText}`)
      }
      const data = await response.json()
      
      const transformedIssues: DashboardItem[] = data.issues?.map((issue: GitHubIssue) => ({
        issue,
        scope_session: null,
        execution_session: null
      })) || []
      
      setIssues(transformedIssues)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch issues')
      console.error('Error fetching issues:', err)
    } finally {
      setLoading(false)
    }
  }

  const scopeIssue = async (issueId: number) => {
    try {
      console.log(`Starting scope for issue ${issueId}`)
      setScopingIssues(prev => new Set(prev).add(issueId))
      
      const response = await fetch(`${API_BASE}/issues/${issueId}/scope`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`Failed to scope issue: ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('Scoping session created:', data)
      
      setIssues(prev => prev.map(item => 
        item.issue.id === issueId 
          ? { 
              ...item, 
              scope_session: { 
                session_id: data.session_id, 
                status: data.status,
                confidence_score: null,
                action_plan: null,
                created_at: new Date().toISOString()
              } 
            }
          : item
      ))
      
      startPollingForConfidence(issueId)
    } catch (err) {
      console.error('Error scoping issue:', err)
      setScopingIssues(prev => {
        const newSet = new Set(prev)
        newSet.delete(issueId)
        return newSet
      })
      setError(err instanceof Error ? err.message : 'Failed to scope issue')
    }
  }

  const startPollingForConfidence = (issueId: number) => {
    console.log(`Starting polling for issue ${issueId}`)
    const pollInterval = setInterval(async () => {
      try {
        console.log(`Polling for confidence score for issue ${issueId}`)
        const response = await fetch(`${API_BASE}/issues/${issueId}`)
        
        if (!response.ok) {
          console.error(`Polling failed for issue ${issueId}:`, response.statusText)
          return
        }
        
        const data = await response.json()
        console.log(`Polling response for issue ${issueId}:`, data)
        
        if (data.current_confidence !== "not yet") {
          console.log(`Confidence score received for issue ${issueId}:`, data.current_confidence)
          clearInterval(pollInterval)
          setScopingIssues(prev => {
            const newSet = new Set(prev)
            newSet.delete(issueId)
            return newSet
          })
          
          setIssues(prev => prev.map(item => 
            item.issue.id === issueId && item.scope_session
              ? { 
                  ...item, 
                  scope_session: { 
                    ...item.scope_session,
                    confidence_score: data.current_confidence,
                    status: 'completed'
                  } 
                }
              : item
          ))
        }
      } catch (err) {
        console.error(`Error polling for issue ${issueId}:`, err)
      }
    }, 10000)
    
    setTimeout(() => {
      clearInterval(pollInterval)
      setScopingIssues(prev => {
        const newSet = new Set(prev)
        newSet.delete(issueId)
        return newSet
      })
    }, 300000)
  }

  const verifyInstallation = async () => {
    if (!installationId.trim()) {
      setVerificationStatus('error')
      setVerificationMessage('Please enter an installation ID')
      return
    }

    setVerificationStatus('loading')
    try {
      const response = await fetch(`${API_BASE}/verify-installation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ installation_id: installationId.trim() })
      })

      const data = await response.json()
      
      if (response.ok && data.success) {
        setVerificationStatus('success')
        setVerificationMessage(data.message)
        setVerifiedUsername(data.username)
      } else {
        setVerificationStatus('error')
        setVerificationMessage(data.detail || 'Verification failed')
      }
    } catch (err) {
      setVerificationStatus('error')
      setVerificationMessage('Network error occurred')
    }
  }

  const resetModal = () => {
    setInstallationId('')
    setVerificationStatus('idle')
    setVerificationMessage('')
    setVerifiedUsername('')
  }

  const getStatusBadge = (status: string | null) => {
    const variant = status === 'completed' ? 'default' : 
                   status === 'running' ? 'secondary' : 
                   status === 'failed' ? 'destructive' : 'outline'
    return <Badge variant={variant}>{status || 'pending'}</Badge>
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 70) {
      return 'bg-green-500'
    } else if (score >= 40) {
      return 'bg-amber-500'
    } else {
      return 'bg-red-500'
    }
  }


  useEffect(() => {
    fetchRepositories()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Github className="h-8 w-8" />
                GitHub Issues Automation
              </h1>
              <p className="text-gray-600">
                Automate GitHub issue analysis and resolution using Devin AI
              </p>
            </div>
            <Button
              onClick={() => {
                resetModal()
                setIsModalOpen(true)
              }}
              className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Github className="h-4 w-4 mr-2" />
              Add GitHub User
            </Button>
          </div>
        </div>


        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Repository Settings</CardTitle>
            <CardDescription>
              Enter the GitHub repository details to fetch issues
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 items-end">
              <div className="w-96">
                <Label htmlFor="repository">Repository</Label>
                <select
                  id="repository"
                  value={selectedRepository}
                  onChange={(e) => setSelectedRepository(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select a repository...</option>
                  {repositories.map((repo) => (
                    <option key={repo.full_name} value={repo.full_name}>
                      {repo.full_name}
                    </option>
                  ))}
                </select>
              </div>
              <Button 
                onClick={fetchIssues} 
                disabled={loading || !selectedRepository}
                className="bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {loading ? 'Loading...' : 'Fetch Issues'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {error && (
          <Card className="mb-6 border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-700">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="space-y-4">
          {issues.length === 0 && !loading && (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-gray-500">
                  No issues found. Click "Fetch Issues" to load issues from the repository.
                </p>
              </CardContent>
            </Card>
          )}

          {issues.map((item) => (
            <Card key={item.issue.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-1 flex items-center gap-2">
                      <a 
                        href={item.issue.html_url || `https://github.com/${selectedRepository}/issues/${item.issue.number}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        {item.issue.title}
                      </a>
                      <Badge variant="outline">#{item.issue.number}</Badge>
                      <Badge 
                        variant="outline"
                        className={item.issue.state === 'open' 
                          ? 'border-red-500 text-red-700 bg-red-50' 
                          : 'border-purple-500 text-purple-700 bg-purple-50'
                        }
                      >
                        {item.issue.state}
                      </Badge>
                    </CardTitle>
                  </div>
                  
                  <div className="flex-shrink-0 ml-4 flex items-center gap-2">
                    {scopingIssues.has(item.issue.id) ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                        <span className="text-sm text-gray-600">scoping in progress...</span>
                      </div>
                    ) : item.scope_session ? (
                      <div className="flex items-center">
                        {item.scope_session.status !== 'completed' && item.scope_session.confidence_score === null && getStatusBadge(item.scope_session.status)}
                        {item.scope_session.confidence_score !== null && (
                          <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${getConfidenceColor(item.scope_session.confidence_score)}`}></div>
                            <p className="text-xs text-gray-600">
                              Confidence: {item.scope_session.confidence_score}%
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => scopeIssue(item.issue.id)}
                      >
                        <Play className="h-3 w-3 mr-1" />
                        Scope with Devin
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 text-sm line-clamp-3">
                  {item.issue.body || 'No description provided'}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* GitHub User Setup Modal */}
      <Dialog open={isModalOpen} onOpenChange={(open) => {
        setIsModalOpen(open)
        if (!open) resetModal()
      }}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add GitHub User</DialogTitle>
            <DialogDescription>
              Follow these steps to add a new GitHub user to the automation system
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Step 1 */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">1</span>
                Install GitHub App
              </h3>
              <p className="text-sm text-gray-600">
                Click the button below to install our GitHub App on your repositories:
              </p>
              <a
                href="https://github.com/apps/devin-issues-integration-app"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
              >
                <Github className="h-4 w-4 mr-2" />
                Install GitHub App
              </a>
              <img 
                src="/screenshots/github-app-main.png" 
                alt="GitHub App installation page"
                className="w-full border rounded-md"
              />
            </div>

            {/* Step 2 */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">2</span>
                Select Repositories
              </h3>
              <p className="text-sm text-gray-600">
                Choose which repositories you want to share with Devin:
              </p>
              <img 
                src="/screenshots/repository-selection.png" 
                alt="Repository selection page"
                className="w-full border rounded-md"
              />
            </div>

            {/* Step 3 */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <span className="bg-blue-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-sm">3</span>
                Copy Installation ID
              </h3>
              <p className="text-sm text-gray-600">
                After installation, copy the installation ID from the URL bar:
              </p>
              <img 
                src="/screenshots/installation-url.png" 
                alt="Installation ID in URL"
                className="w-full border rounded-md"
              />
              
              <div className="space-y-2">
                <Label htmlFor="installation-id">Installation ID</Label>
                <Input
                  id="installation-id"
                  value={installationId}
                  onChange={(e) => setInstallationId(e.target.value)}
                  placeholder="Enter installation ID (e.g., 73911812)"
                  disabled={verificationStatus === 'loading'}
                />
              </div>
              
              <Button 
                onClick={verifyInstallation}
                disabled={verificationStatus === 'loading' || !installationId.trim()}
                className="w-full"
              >
                {verificationStatus === 'loading' ? 'Verifying...' : 'Verify Installation'}
              </Button>
              
              {verificationStatus === 'success' && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                  <p className="text-sm text-green-800 font-medium">✅ Success!</p>
                  <p className="text-sm text-green-700">
                    User <strong>{verifiedUsername}</strong> has been added successfully.
                  </p>
                </div>
              )}
              
              {verificationStatus === 'error' && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                  <p className="text-sm text-red-800 font-medium">❌ Error</p>
                  <p className="text-sm text-red-700">{verificationMessage}</p>
                </div>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default App

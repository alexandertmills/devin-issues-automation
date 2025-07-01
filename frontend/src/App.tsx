import { useState, useEffect } from 'react'
import { Github, Play, CheckCircle, Clock, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import './App.css'

interface GitHubIssue {
  id: number
  github_issue_id: number
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

function App() {
  const [issues, setIssues] = useState<DashboardItem[]>([])
  const [loading, setLoading] = useState(false)
  const [owner, setOwner] = useState('octocat')
  const [repo, setRepo] = useState('Hello-World')
  const [githubToken, setGithubToken] = useState('')
  const [githubAppStatus, setGithubAppStatus] = useState<{
    configured: boolean
    message: string
    missing_credentials?: string[]
    app_id?: string
    installation_id?: string
    account?: string
  } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const API_BASE = 'http://localhost:8000'

  const fetchGithubAppStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/github-app-status`)
      const data = await response.json()
      setGithubAppStatus(data)
    } catch (error) {
      console.error('Error fetching GitHub App status:', error)
      setGithubAppStatus({
        configured: false,
        message: 'Error fetching GitHub App status'
      })
    }
  }

  const fetchIssues = async () => {
    setLoading(true)
    setError(null)
    try {
      const url = `${API_BASE}/issues/${owner}/${repo}?state=open&limit=10`
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      
      if (githubToken) {
        headers['X-GitHub-Token'] = githubToken
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
    } catch (err) {
      console.error('Error scoping issue:', err)
      setError(err instanceof Error ? err.message : 'Failed to scope issue')
    }
  }

  const executeIssue = async (issueId: number) => {
    try {
      const response = await fetch(`${API_BASE}/issues/${issueId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`Failed to execute issue: ${response.statusText}`)
      }
      
      const data = await response.json()
      console.log('Execution session created:', data)
      
      setIssues(prev => prev.map(item => 
        item.issue.id === issueId 
          ? { 
              ...item, 
              execution_session: { 
                session_id: data.session_id, 
                status: data.status,
                confidence_score: null,
                action_plan: null,
                created_at: new Date().toISOString()
              } 
            }
          : item
      ))
    } catch (err) {
      console.error('Error executing issue:', err)
      setError(err instanceof Error ? err.message : 'Failed to execute issue')
    }
  }

  const getStatusIcon = (status: string | null) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string | null) => {
    const variant = status === 'completed' ? 'default' : 
                   status === 'running' ? 'secondary' : 
                   status === 'failed' ? 'destructive' : 'outline'
    return <Badge variant={variant}>{status || 'pending'}</Badge>
  }

  useEffect(() => {
    fetchGithubAppStatus()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
            <Github className="h-8 w-8" />
            GitHub Issues Automation
          </h1>
          <p className="text-gray-600">
            Automate GitHub issue analysis and resolution using Devin AI
          </p>
        </div>

        {githubAppStatus && (
          <Card className={`mb-6 ${
            githubAppStatus.configured 
              ? 'border-green-200 bg-green-50' 
              : 'border-yellow-200 bg-yellow-50'
          }`}>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  githubAppStatus.configured ? 'bg-green-500' : 'bg-yellow-500'
                }`}></div>
                <h3 className="font-medium">
                  {githubAppStatus.configured ? 'GitHub App Connected' : 'GitHub App Not Configured'}
                </h3>
              </div>
              <p className="text-sm text-gray-600 mt-1">{githubAppStatus.message}</p>
              {githubAppStatus.configured && githubAppStatus.account && (
                <p className="text-sm text-gray-500 mt-1">
                  Connected to: {githubAppStatus.account}
                </p>
              )}
              {!githubAppStatus.configured && githubAppStatus.missing_credentials && (
                <div className="mt-2">
                  <p className="text-sm text-gray-600">Missing credentials:</p>
                  <ul className="text-sm text-gray-500 list-disc list-inside">
                    {githubAppStatus.missing_credentials.map(cred => (
                      <li key={cred}>{cred}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Repository Settings</CardTitle>
            <CardDescription>
              Enter the GitHub repository details to fetch issues
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <Label htmlFor="owner">Repository Owner</Label>
                  <Input
                    id="owner"
                    value={owner}
                    onChange={(e) => setOwner(e.target.value)}
                    placeholder="octocat"
                  />
                </div>
                <div className="flex-1">
                  <Label htmlFor="repo">Repository Name</Label>
                  <Input
                    id="repo"
                    value={repo}
                    onChange={(e) => setRepo(e.target.value)}
                    placeholder="Hello-World"
                  />
                </div>
                <Button onClick={fetchIssues} disabled={loading}>
                  {loading ? 'Loading...' : 'Fetch Issues'}
                </Button>
              </div>
              <div>
                <Label htmlFor="github-token">GitHub Token (Optional)</Label>
                <Input
                  id="github-token"
                  type="password"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx (for private repos)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty for public repositories. Required for private repositories.
                </p>
              </div>
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
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg mb-1">
                      {item.issue.title}
                    </CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      <Badge variant="outline">#{item.issue.github_issue_id}</Badge>
                      <span>{item.issue.repository}</span>
                      <Badge variant={item.issue.state === 'open' ? 'default' : 'secondary'}>
                        {item.issue.state}
                      </Badge>
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="mb-4">
                  <p className="text-gray-700 text-sm line-clamp-3">
                    {item.issue.body || 'No description provided'}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-sm">Scoping Session</h4>
                      {item.scope_session && getStatusIcon(item.scope_session.status)}
                    </div>
                    {item.scope_session ? (
                      <div className="space-y-1">
                        {getStatusBadge(item.scope_session.status)}
                        {item.scope_session.confidence_score && (
                          <p className="text-xs text-gray-600">
                            Confidence: {item.scope_session.confidence_score}%
                          </p>
                        )}
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => scopeIssue(item.issue.id)}
                        className="w-full"
                      >
                        <Play className="h-3 w-3 mr-1" />
                        Start Scoping
                      </Button>
                    )}
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-sm">Execution Session</h4>
                      {item.execution_session && getStatusIcon(item.execution_session.status)}
                    </div>
                    {item.execution_session ? (
                      <div className="space-y-1">
                        {getStatusBadge(item.execution_session.status)}
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => executeIssue(item.issue.id)}
                        disabled={!item.scope_session}
                        className="w-full"
                      >
                        <Play className="h-3 w-3 mr-1" />
                        Start Execution
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

export default App

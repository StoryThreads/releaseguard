import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { ProjectList } from './components/ProjectList';
import { ProjectDetails } from './components/ProjectDetails';
import { PullRequestList } from './components/PullRequestList';
import { PullRequestDetails } from './components/PullRequestDetails';
import { AnalysisProgressModal } from './components/AnalysisProgressModal';
import { SourceConfigModal } from './components/SourceConfigModal';
import { WebhookSimulator } from './components/WebhookSimulator';
import type { Project, Source } from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState<'projects' | 'pull-requests' | 'webhooks'>('projects');
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [selectedChangeId, setSelectedChangeId] = useState<number | null>(null);

  // Modals state
  const [isAnalysisModalOpen, setIsAnalysisModalOpen] = useState(false);
  const [targetAnalysisProject, setTargetAnalysisProject] = useState<Project | undefined>();
  const [targetAnalysisSource, setTargetAnalysisSource] = useState<Source | undefined>();

  const [isSourceModalOpen, setIsSourceModalOpen] = useState(false);
  const [targetSourceProject, setTargetSourceProject] = useState<Project | null>(null);

  const handleOpenSourceModal = (project: Project) => {
    setTargetSourceProject(project);
    setIsSourceModalOpen(true);
  };

  const handleOpenAnalysisModal = (project?: Project, source?: Source) => {
    setTargetAnalysisProject(project);
    setTargetAnalysisSource(source);
    setIsAnalysisModalOpen(true);
  };

  const handleAnalysisCompleted = (changeId: number) => {
    setSelectedChangeId(changeId);
    setCurrentTab('pull-requests');
  };

  return (
    <div className="app-container">
      {/* Navbar */}
      <Navbar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setCurrentTab(tab);
          if (tab === 'projects') setSelectedProjectId(null);
          if (tab === 'pull-requests') setSelectedChangeId(null);
        }}
        onOpenAnalysisModal={() => handleOpenAnalysisModal()}
      />

      {/* Main Content Area */}
      <main className="main-content">
        {/* Tab 1: Projects */}
        {currentTab === 'projects' && (
          <>
            {selectedProjectId ? (
              <ProjectDetails
                projectId={selectedProjectId}
                onBack={() => setSelectedProjectId(null)}
                onSelectChange={(changeId) => {
                  setSelectedChangeId(changeId);
                  setCurrentTab('pull-requests');
                }}
                onOpenSourceModal={handleOpenSourceModal}
                onOpenAnalysisModal={handleOpenAnalysisModal}
              />
            ) : (
              <ProjectList
                onSelectProject={(id) => setSelectedProjectId(id)}
                onOpenSourceModal={handleOpenSourceModal}
                onBrowsePullRequests={(projectId) => {
                  setSelectedProjectId(projectId || null);
                  setCurrentTab('pull-requests');
                }}
                onOpenAnalysisModal={() => handleOpenAnalysisModal()}
              />
            )}
          </>
        )}

        {/* Tab 2: Pull Requests */}
        {currentTab === 'pull-requests' && (
          <>
            {selectedChangeId ? (
              <PullRequestDetails
                changeId={selectedChangeId}
                onBack={() => setSelectedChangeId(null)}
              />
            ) : (
              <PullRequestList
                selectedProjectId={selectedProjectId || undefined}
                onSelectChange={(changeId) => setSelectedChangeId(changeId)}
                onOpenAnalysisModal={() => handleOpenAnalysisModal()}
              />
            )}
          </>
        )}

        {/* Tab 3: Webhook Automation & Simulator */}
        {currentTab === 'webhooks' && <WebhookSimulator />}
      </main>

      {/* Modals */}
      <AnalysisProgressModal
        isOpen={isAnalysisModalOpen}
        onClose={() => setIsAnalysisModalOpen(false)}
        defaultProject={targetAnalysisProject}
        defaultSource={targetAnalysisSource}
        onAnalysisCompleted={handleAnalysisCompleted}
      />

      {targetSourceProject && (
        <SourceConfigModal
          isOpen={isSourceModalOpen}
          project={targetSourceProject}
          onClose={() => setIsSourceModalOpen(false)}
          onSourceAdded={() => {
            // Project details or list will automatically refresh on next focus/render
          }}
        />
      )}
    </div>
  );
}

export default App;

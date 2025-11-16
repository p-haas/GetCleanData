import { DatasetProvider, useDataset } from '@/context/DatasetContext';
import { Stepper } from '@/components/Stepper';
import { UploadStep } from '@/components/upload/UploadStep';
import { UnderstandingStep } from '@/components/understanding/UnderstandingStep';
import { AnalysisStep } from '@/components/analysis/AnalysisStep';
import { Button } from '@/components/ui/button';
import { RotateCcw } from 'lucide-react';

const steps = [
  { label: 'Upload', description: 'Upload dataset' },
  { label: 'Understand', description: 'Review & enrich' },
  { label: 'Analyze', description: 'Clean & fix' },
];

const DataCleaningApp = () => {
  const { currentStep, setCurrentStep, resetDataset } = useDataset();

  const handleReset = () => {
    if (confirm('Are you sure you want to start over? All progress will be lost.')) {
      resetDataset();
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-foreground">DataClean AI</h1>
              <p className="text-sm text-muted-foreground">AI-powered dataset cleaning</p>
            </div>
            {currentStep > 0 && (
              <Button variant="outline" onClick={handleReset} size="sm">
                <RotateCcw className="w-4 h-4 mr-2" />
                Start Over
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Stepper
          steps={steps}
          currentStep={currentStep}
          onStepClick={setCurrentStep}
        />

        <div className="mt-8">
          {currentStep === 0 && <UploadStep />}
          {currentStep === 1 && <UnderstandingStep />}
          {currentStep === 2 && <AnalysisStep />}
        </div>
      </main>

      <footer className="border-t border-border mt-16 py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>Powered by AI agents and LLMs • Built for data scientists and business users</p>
        </div>
      </footer>
    </div>
  );
};

const Index = () => {
  return (
    <DatasetProvider>
      <DataCleaningApp />
    </DatasetProvider>
  );
};

export default Index;

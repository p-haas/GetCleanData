import { useState, useCallback } from 'react';
import { Upload, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useDataset } from '@/context/DatasetContext';
import { apiClient } from '@/lib/apiClient';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

export const UploadStep = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setDatasetId, setFileName, setCurrentStep } = useDataset();
  const { toast } = useToast();

  const validateFile = (file: File): string | null => {
    if (!file.name.endsWith('.csv')) {
      return 'Please upload a CSV file';
    }
    if (file.size > 500 * 1024 * 1024) {
      return 'File size must be less than 500MB';
    }
    return null;
  };

  const handleFile = async (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setIsUploading(true);

    try {
      const { datasetId } = await apiClient.uploadDataset(file);
      setDatasetId(datasetId);
      setFileName(file.name);
      
      toast({
        title: 'Upload successful',
        description: `${file.name} uploaded successfully`,
      });

      // Move to next step
      setTimeout(() => {
        setCurrentStep(1);
      }, 500);
    } catch (err) {
      setError('Failed to upload file. Please try again.');
      toast({
        title: 'Upload failed',
        description: 'There was an error uploading your file',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-foreground mb-3">
          Clean Your Data with AI
        </h1>
        <p className="text-lg text-muted-foreground">
          Upload a CSV and our AI agents will understand and clean your data
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          'border-2 border-dashed rounded-lg p-12 transition-all duration-300',
          isDragging && 'border-primary bg-primary/5 scale-[1.02]',
          !isDragging && 'border-border hover:border-primary/50',
          isUploading && 'opacity-50 pointer-events-none'
        )}
      >
        <div className="flex flex-col items-center text-center">
          <div className={cn(
            'w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors',
            isDragging ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
          )}>
            {isUploading ? (
              <div className="w-6 h-6 border-2 border-current border-t-transparent rounded-full animate-spin" />
            ) : (
              <Upload className="w-8 h-8" />
            )}
          </div>

          <h3 className="text-lg font-semibold mb-2">
            {isUploading ? 'Uploading...' : 'Drop your CSV file here'}
          </h3>
          <p className="text-sm text-muted-foreground mb-6">
            or click to browse from your computer
          </p>

          <input
            type="file"
            id="file-upload"
            className="hidden"
            accept=".csv"
            onChange={handleFileInput}
            disabled={isUploading}
          />
          <Button
            asChild
            variant="default"
            size="lg"
            disabled={isUploading}
          >
            <label htmlFor="file-upload" className="cursor-pointer">
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Browse Files
            </label>
          </Button>

          <div className="mt-8 pt-6 border-t border-border w-full">
            <p className="text-xs text-muted-foreground">
              Supported format: CSV • Maximum file size: 500MB
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { DatasetUnderstanding, AnalysisResult } from '@/types/dataset';

interface DatasetContextType {
  currentStep: number;
  setCurrentStep: (step: number) => void;
  datasetId: string | null;
  setDatasetId: (id: string | null) => void;
  fileName: string | null;
  setFileName: (name: string | null) => void;
  understanding: DatasetUnderstanding | null;
  setUnderstanding: (understanding: DatasetUnderstanding | null) => void;
  userContext: string;
  setUserContext: (context: string) => void;
  analysisResult: AnalysisResult | null;
  setAnalysisResult: (result: AnalysisResult | null) => void;
  resetDataset: () => void;
}

const DatasetContext = createContext<DatasetContextType | undefined>(undefined);

export const DatasetProvider = ({ children }: { children: ReactNode }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [datasetId, setDatasetId] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [understanding, setUnderstanding] = useState<DatasetUnderstanding | null>(null);
  const [userContext, setUserContext] = useState('');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const resetDataset = () => {
    setCurrentStep(0);
    setDatasetId(null);
    setFileName(null);
    setUnderstanding(null);
    setUserContext('');
    setAnalysisResult(null);
  };

  return (
    <DatasetContext.Provider
      value={{
        currentStep,
        setCurrentStep,
        datasetId,
        setDatasetId,
        fileName,
        setFileName,
        understanding,
        setUnderstanding,
        userContext,
        setUserContext,
        analysisResult,
        setAnalysisResult,
        resetDataset,
      }}
    >
      {children}
    </DatasetContext.Provider>
  );
};

export const useDataset = () => {
  const context = useContext(DatasetContext);
  if (context === undefined) {
    throw new Error('useDataset must be used within a DatasetProvider');
  }
  return context;
};

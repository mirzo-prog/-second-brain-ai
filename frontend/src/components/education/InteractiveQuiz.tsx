import React, { useState } from 'react';
import { CheckCircle2, XCircle, HelpCircle, RotateCcw, Award } from 'lucide-react';

export interface QuizItem {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

interface InteractiveQuizProps {
  quizJson?: string;
  lessonTitle: string;
  onComplete?: (score: number, total: number) => void;
}

export const InteractiveQuiz: React.FC<InteractiveQuizProps> = ({
  quizJson,
  lessonTitle,
  onComplete,
}) => {
  let questions: QuizItem[] = [];
  try {
    if (quizJson) {
      questions = JSON.parse(quizJson);
    }
  } catch (e) {
    questions = [];
  }

  // Fallback questions if none provided
  if (!questions || questions.length === 0) {
    questions = [
      {
        question: `Какова ключевая цель изучения темы «${lessonTitle}»?`,
        options: [
          'Понимание фундаментальных принципов и практическое применение',
          'Только механическое заучивание терминов',
          'Игнорирование реальных практических задач',
          'Использование устаревших методик без проверки',
        ],
        correct_index: 0,
        explanation:
          'Глубокое освоение темы строится на осознании базовых концепций и их непосредственной проверке на практике.',
      },
    ];
  }

  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({});
  const [submitted, setSubmitted] = useState<Record<number, boolean>>({});

  const handleSelectOption = (qIndex: number, optIndex: number) => {
    if (submitted[qIndex]) return; // locked after checking
    setSelectedAnswers((prev) => ({ ...prev, [qIndex]: optIndex }));
  };

  const handleCheckAnswer = (qIndex: number) => {
    if (selectedAnswers[qIndex] === undefined) return;
    setSubmitted((prev) => ({ ...prev, [qIndex]: true }));

    // Check if all are submitted
    const newSubmitted = { ...submitted, [qIndex]: true };
    if (Object.keys(newSubmitted).length === questions.length) {
      let correctCount = 0;
      questions.forEach((q, idx) => {
        if (selectedAnswers[idx] === q.correct_index) correctCount++;
      });
      onComplete?.(correctCount, questions.length);
    }
  };

  const handleResetQuiz = () => {
    setSelectedAnswers({});
    setSubmitted({});
  };

  const totalSubmitted = Object.keys(submitted).length;
  const isFinished = totalSubmitted === questions.length;
  let correctCount = 0;
  questions.forEach((q, idx) => {
    if (submitted[idx] && selectedAnswers[idx] === q.correct_index) correctCount++;
  });

  return (
    <div className="my-8 rounded-2xl bg-dark-850 border border-dark-700/80 p-6 sm:p-8 shadow-xl">
      <div className="flex items-center justify-between pb-5 border-b border-dark-700">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-primary-500/10 text-primary-400">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Интерактивный тест для закрепления</h3>
            <p className="text-xs text-dark-400">
              Проверьте понимание материала темы: ответьте на вопросы и изучите пояснения
            </p>
          </div>
        </div>

        {isFinished && (
          <button
            onClick={handleResetQuiz}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dark-750 hover:bg-dark-700 text-xs text-dark-200 hover:text-white transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Пройти заново</span>
          </button>
        )}
      </div>

      {/* Questions list */}
      <div className="mt-6 space-y-6">
        {questions.map((q, qIndex) => {
          const isQSubmitted = !!submitted[qIndex];
          const chosenOpt = selectedAnswers[qIndex];
          const isCorrect = chosenOpt === q.correct_index;

          return (
            <div
              key={qIndex}
              className="p-5 rounded-xl bg-dark-900 border border-dark-750 transition"
            >
              <div className="flex items-start gap-2.5 mb-4">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-dark-800 text-primary-400 font-bold text-xs flex items-center justify-center">
                  {qIndex + 1}
                </span>
                <h4 className="text-sm font-semibold text-white leading-snug">{q.question}</h4>
              </div>

              {/* Options */}
              <div className="space-y-2 mb-4">
                {q.options.map((opt, optIndex) => {
                  const isSelected = chosenOpt === optIndex;
                  let btnStyle = 'border-dark-750 bg-dark-800/60 text-dark-200 hover:border-dark-600';

                  if (isQSubmitted) {
                    if (optIndex === q.correct_index) {
                      btnStyle = 'border-emerald-500/60 bg-emerald-500/15 text-emerald-200';
                    } else if (isSelected && !isCorrect) {
                      btnStyle = 'border-red-500/60 bg-red-500/15 text-red-200';
                    } else {
                      btnStyle = 'border-dark-800 bg-dark-850/40 text-dark-500 opacity-60';
                    }
                  } else if (isSelected) {
                    btnStyle = 'border-primary-500 bg-primary-500/15 text-white ring-1 ring-primary-500';
                  }

                  return (
                    <button
                      key={optIndex}
                      onClick={() => handleSelectOption(qIndex, optIndex)}
                      disabled={isQSubmitted}
                      className={`w-full text-left p-3 rounded-xl border text-xs sm:text-sm font-medium transition flex items-center justify-between gap-3 ${btnStyle}`}
                    >
                      <span>{opt}</span>
                      {isQSubmitted && optIndex === q.correct_index && (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      )}
                      {isQSubmitted && isSelected && !isCorrect && (
                        <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Action / Explanation */}
              {!isQSubmitted ? (
                <button
                  onClick={() => handleCheckAnswer(qIndex)}
                  disabled={chosenOpt === undefined}
                  className={`px-4 py-2 rounded-xl text-xs font-semibold transition ${
                    chosenOpt !== undefined
                      ? 'bg-primary-500 hover:bg-primary-600 text-white shadow-md shadow-primary-500/20'
                      : 'bg-dark-800 text-dark-500 cursor-not-allowed'
                  }`}
                >
                  Проверить ответ
                </button>
              ) : (
                <div
                  className={`p-3.5 rounded-xl border text-xs leading-relaxed ${
                    isCorrect
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                      : 'bg-dark-800/90 border-dark-700 text-dark-300'
                  }`}
                >
                  <p className="font-semibold mb-1">
                    {isCorrect ? 'Верно! Отличная работа.' : 'Пояснение к вопросу:'}
                  </p>
                  <p>{q.explanation}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Finished Summary Score */}
      {isFinished && (
        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-primary-500/10 to-emerald-500/10 border border-primary-500/30 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-primary-500/20 text-primary-400">
              <Award className="w-6 h-6" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">Тест завершён!</h4>
              <p className="text-xs text-dark-300">
                Ваш результат: <span className="font-bold text-primary-400">{correctCount}</span> из{' '}
                <span className="font-bold text-white">{questions.length}</span> (
                {Math.round((correctCount / questions.length) * 100)}%)
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

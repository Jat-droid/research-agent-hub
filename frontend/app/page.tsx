
"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
export default function Home() {
  const [topic, setTopic] = useState("");
  const [report, setReport] = useState("");
  const [logs, setLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // Ref to auto-scroll the terminal logs
  const logsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  const generateReport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsLoading(true);
    setReport(""); // Clear previous report
    setLogs([]);   // Clear previous logs

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/generate-report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok || !response.body) {
        throw new Error("Failed to connect to the backend");
      }

      // 1. Create a reader for the Server-Sent Events stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let done = false;

      // 2. Loop through the incoming stream chunks
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;

        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          
          // SSE sends data formatted as "data: {...}\n\n"
          const lines = chunk.split("\n\n");
          
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const parsedData = JSON.parse(line.replace("data: ", ""));

                // Handle Live Logs
                if (parsedData.type === "log") {
                  setLogs((prev) => [...prev, parsedData.message]);
                } 
                // Handle Final Report
                else if (parsedData.type === "done") {
                  setReport(parsedData.report_markdown);
                } 
                // Handle Errors
                else if (parsedData.type === "error") {
                  setLogs((prev) => [...prev, `❌ [CRITICAL ERROR]: ${parsedData.message}`]);
                  console.error("Agent Error:", parsedData.message);
                }
              } catch (parseError) {
                console.error("Failed to parse stream chunk:", line);
              }
            }
          }
        }
      }
    } catch (error) {
      setReport("### Error\nSomething went wrong connecting to the AI agents. Ensure your backend server is running!");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-8 md:p-16 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* Header Section */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            Multi-Agent <span className="text-blue-500">Research Engine</span>
          </h1>
          <p className="text-gray-400">
            Enter a complex topic. Our AI agents will autonomously plan, scrape, synthesize, and write a cited report.
          </p>
        </div>

        {/* Input Form */}
        <form onSubmit={generateReport} className="flex flex-col md:flex-row gap-4">
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., The impact of quantum computing on modern cryptography"
            className="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-6 py-4 text-lg focus:outline-none focus:border-blue-500 transition-colors placeholder:text-gray-600"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !topic.trim()}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-500 text-white font-semibold px-8 py-4 rounded-lg transition-colors"
          >
            {isLoading ? "Agents Working..." : "Generate Report"}
          </button>
        </form>

        {/* Live Agent Terminal Logs */}
        {(logs.length > 0 || isLoading) && !report && (
          <div className="bg-black border border-gray-800 rounded-xl p-6 font-mono text-sm h-80 overflow-y-auto flex flex-col gap-3 shadow-2xl">
            {logs.map((log, index) => {
              // Simple color coding based on agent type or action
              let textColor = "text-gray-300";
              if (log.includes("❌")) textColor = "text-red-400";
              if (log.includes("✅") || log.includes("🏁")) textColor = "text-green-400";
              if (log.includes("🗺️") || log.includes("⚙️")) textColor = "text-purple-400";
              if (log.includes("🧠") || log.includes("⚖️")) textColor = "text-yellow-400";
              if (log.includes("🚀") || log.includes("📝")) textColor = "text-blue-400";

              return (
                <div key={index} className={`${textColor} leading-relaxed tracking-wide`}>
                  {log}
                </div>
              );
            })}
            
            {/* Blinking cursor effect while loading */}
            {isLoading && (
              <div className="flex items-center space-x-2 mt-2 text-blue-500 animate-pulse">
                <div className="w-2 h-4 bg-blue-500"></div>
                <span className="text-gray-500 italic">Awaiting agent response...</span>
              </div>
            )}
            <div ref={logsEndRef} />
          </div>
        )}

      {/* Markdown Output Area & Export Buttons */}
        {report && !isLoading && (
          <div className="space-y-6">
            {/* Export Toolbar */}
            <div className="flex gap-4 justify-end">
              <button
                onClick={async () => {
                 const res = await fetch(`${API_BASE_URL}/api/v1/export/pdf`, {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic, markdown: report })
                  });
                  const blob = await res.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url; a.download = `${topic}_Report.pdf`; a.click();
                }}
                className="bg-red-600 hover:bg-red-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-2 shadow-lg"
              >
                📄 Download PDF
              </button>
              <button
                onClick={async () => {
                  const res = await fetch(`${API_BASE_URL}/api/v1/export/word`, {
                    method: "POST", headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ topic, markdown: report })
                  });
                  const blob = await res.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url; a.download = `${topic}_Report.docx`; a.click();
                }}
                className="bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors flex items-center gap-2 shadow-lg"
              >
                📝 Download Word
              </button>
            </div>

            {/* The Report */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 md:p-12 shadow-2xl">
              <ReactMarkdown
                components={{
                  h1: ({node, ...props}) => <h1 className="text-3xl font-bold mb-6 text-white" {...props} />,
                  h2: ({node, ...props}) => <h2 className="text-2xl font-semibold mt-10 mb-4 text-blue-400 border-b border-gray-800 pb-2" {...props} />,
                  h3: ({node, ...props}) => <h3 className="text-xl font-medium mt-6 mb-3 text-gray-200" {...props} />,
                  p: ({node, ...props}) => <p className="mb-5 leading-relaxed text-gray-300 text-lg" {...props} />,
                  ul: ({node, ...props}) => <ul className="list-disc pl-6 mb-5 text-gray-300 space-y-2" {...props} />,
                  li: ({node, ...props}) => <li className="leading-relaxed" {...props} />,
                  a: ({node, ...props}) => <a className="text-blue-400 hover:text-blue-300 underline underline-offset-4" target="_blank" rel="noopener noreferrer" {...props} />,
                  strong: ({node, ...props}) => <strong className="font-semibold text-gray-100" {...props} />,
                }}
              >
                {report}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
"use client";
import { useState } from "react";

export default function Home() {
  const [testCase, setTestCase] = useState("");
  const [logs, setLogs] = useState([]);
  const [finalResult, setFinalResult] = useState(null);
  const [eventSource, setEventSource] = useState(null);

  const runTest = async () => {
    if (eventSource) {
      eventSource.close();
      setEventSource(null);
    }
    setLogs([]);
    setFinalResult(null);

    if (!testCase.trim()) {
      alert("Please enter a valid test case name");
      return;
    }

    const newEventSource = new EventSource(`http://127.0.0.1:5000/run-test/${testCase}`);
    setEventSource(newEventSource);

    newEventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.step) {
          const formattedStep = typeof data.step === "object" 
            ? JSON.stringify(data.step, null, 2)  // Pretty-print JSON
            : data.step;
          
          setLogs((prevLogs) => [...prevLogs, formattedStep]);
        } else if (data.result) {
          setFinalResult(data.result);
          setLogs((prevLogs) => [...prevLogs, "✅ Test Completed"]);
          newEventSource.close();
          setEventSource(null);
        } else if (data.error) {
          setLogs((prevLogs) => [...prevLogs, `❌ Error: ${data.error}`]);
          newEventSource.close();
          setEventSource(null);
        }
      } catch (error) {
        console.error("Error parsing event data:", error);
      }
    };

    newEventSource.onerror = () => {
      setLogs((prevLogs) => [...prevLogs, "❌ Connection error. Retrying..."]);
      newEventSource.close();
      setEventSource(null);
    };
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Test Automation Runner</h1>
      <div className="flex gap-2">
        <input
          type="text"
          placeholder="Enter test case name..."
          value={testCase}
          onChange={(e) => setTestCase(e.target.value)}
          className="border p-2 rounded flex-grow"
        />
        <button onClick={runTest} className="p-2 bg-blue-500 text-white rounded">
          Run Test
        </button>
      </div>

      <div className="mt-4 p-4 border rounded bg-gray-100 text-black max-h-80 overflow-auto">
        <h2 className="font-bold mb-2">Execution Logs:</h2>
        <pre className="whitespace-pre-wrap">{logs.join("\n\n")}</pre>
      </div>

      {finalResult && (
        <div className="mt-4 p-4 border rounded bg-green-100 text-black max-h-80 overflow-auto">
          <h2 className="font-bold text-green-800">Final Result:</h2>
          <pre className="whitespace-pre-wrap">{finalResult}</pre>
        </div>
      )}
    </div>
  );
}

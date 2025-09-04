"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { Play, Pause, Upload, Camera, BarChart3, Shield, Wifi, Loader2 ,AlertTriangle,CheckCircle2} from "lucide-react"; // ✅ Added Loader2 icon

type VideoSource = "none" | "camera" | "upload";

// Helper component for the "OR" divider
const OrDivider = () => (
  <div className="flex items-center my-2">
    <div className="flex-grow border-t border-border"></div>
    <span className="flex-shrink mx-2 text-xs text-muted-foreground">OR</span>
    <div className="flex-grow border-t border-border"></div>
  </div>
);

export const SentryDashboard = () => {
  const [source, setSource] = useState<VideoSource>("none");
  const [isPlaying, setIsPlaying] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false); // ✅ NEW: State for connection attempts
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [networkUrl, setNetworkUrl] = useState<string>("");

  const videoRef = useRef<HTMLVideoElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 🔹 Fetch alerts from backend
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:5000/api/alerts");
        setAlerts(res.data);
      } catch (err) {
        console.error("Failed to fetch alerts:", err);
      }
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000);
    return () => clearInterval(interval);
  }, []);

  // ✅ UPDATED: Added isConnecting logic to all camera functions
  const startLocalWebcam = async () => {
    setIsConnecting(true);
    try {
      await axios.post("http://127.0.0.1:5000/api/start_camera", { source: 0 });
      setSource("camera");
      setVideoUrl("http://127.0.0.1:5000/api/video_feed");
    } catch (err: any) {
      console.error("Failed to start local webcam:", err);
      alert(err.response?.data?.error || "Failed to start webcam.");
    } finally {
      setIsConnecting(false);
    }
  };

  const startNetworkStream = async () => {
    if (!networkUrl.trim()) {
      alert("Please enter a network stream URL first.");
      return;
    }
    setIsConnecting(true);
    try {
      await axios.post("http://127.0.0.1:5000/api/start_camera", { source: networkUrl });
      setSource("camera");
      setVideoUrl("http://127.0.0.1:5000/api/video_feed");
    } catch (err: any) {
      console.error("Failed to start network stream:", err);
      alert(err.response?.data?.error || "Failed to connect to stream.");
    } finally {
      setIsConnecting(false);
    }
  };

  const stopCamera = async () => {
    setIsConnecting(false); // Reset connecting state when stopping
    await axios.post("http://127.0.0.1:5000/api/stop_camera");
    setSource("none");
    setVideoUrl(null);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type.startsWith("video/")) {
      setUploadedFile(file);
      setSource("upload");
      setAnalysisResult(null);
      const url = URL.createObjectURL(file);
      setVideoUrl(url);
      if (videoRef.current) {
        videoRef.current.src = url;
      }
    }
  };

  const togglePlayback = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const analyzeVideo = async () => {
    if (!uploadedFile) return;
    setLoading(true);
    setAnalysisResult(null);
    try {
      const formData = new FormData();
      formData.append("file", uploadedFile);
      const res = await fetch("http://127.0.0.1:5000/api/process-video", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setAnalysisResult(data);
    } catch (error) {
      console.error("Error analyzing video:", error);
      setAnalysisResult({ error: "An unexpected error occurred." });
    } finally {
      setLoading(false);
    }
  };

  const generateCameraReport = async () => {
    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/generate-camera-report");
      alert(res.data.status);
    } catch (err: any) {
      console.error("Failed to generate report:", err);
      alert(err.response?.data?.status || "Error generating report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-4 gap-4 p-4">
      <div className="col-span-3 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-primary rounded-lg">
              <Shield className="w-8 h-8 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Sentry AI
              </h1>
              <p className="text-muted-foreground">
                Advanced Surveillance System
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Badge
              variant="outline"
              className="border-tech-glow text-tech-glow"
            >
              <div className="w-2 h-2 bg-tech-glow rounded-full mr-2 animate-pulse" />
              System Active
            </Badge>
            <Button
              variant="outline"
              className="border-tech-glow text-tech-glow hover:bg-tech-glow hover:text-background"
              onClick={() => (window.location.href = "/reports")}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Past Reports
            </Button>
          </div>
        </div>
        {/* Video Card */}
        <Card className="bg-gradient-card shadow-card border-border">
          <CardHeader>
            <CardTitle className="flex justify-between items-center">
              <span>Live Feed</span>
              {source === "camera" && (
                <span className="text-green-500 text-sm">● Recording</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center items-center w-full h-[500px] bg-muted rounded-lg">
            {videoUrl ? (
              source === "camera" ? (
                <img
                  src={videoUrl}
                  alt="Camera feed"
                  className="h-full w-full object-cover rounded-lg"
                />
              ) : (
                <video
                  ref={videoRef}
                  src={videoUrl}
                  controls
                  autoPlay
                  className="h-full w-full object-cover rounded-lg"
                />
              )
            ) : (
              <p className="text-gray-400">No source selected</p>
            )}
          </CardContent>
          {/* Controls for uploaded video */}
          {source === "upload" && uploadedFile && (
            <CardContent className="flex justify-between items-center mt-2">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={togglePlayback}
                  className="border-tech-glow text-tech-glow hover:bg-tech-glow hover:text-background"
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                </Button>
                <span className="text-sm text-muted-foreground">
                  {uploadedFile.name}
                </span>
              </div>
              <div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  className="border-tech-glow text-tech-glow hover:bg-tech-glow hover:text-background"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Video
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!uploadedFile || loading}
                  onClick={analyzeVideo}
                  className="ml-2 border-tech-glow text-tech-glow hover:bg-tech-glow hover:text-background"
                >
                  {loading ? "Analyzing..." : "Analyze Video"}
                </Button>
              </div>
            </CardContent>
          )}
          {/* Analysis Results */}
          {analysisResult && (
            <CardContent className="mt-4 p-4 bg-muted rounded-lg border border-border">
              <h3 className="text-lg font-bold mb-2">Analysis Result</h3>
              {analysisResult.error ? (
                <div className="flex items-center gap-3 p-3 bg-red-900/50 text-red-300 rounded-md">
                  <AlertTriangle className="w-6 h-6" />
                  <div>
                    <p className="font-semibold">An Error Occurred</p>
                    <p className="text-sm">{analysisResult.error}</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3 p-3 bg-green-900/50 text-green-300 rounded-md">
                  <CheckCircle2 className="w-6 h-6" />
                  <div>
                    <p className="font-semibold">{analysisResult.status}</p>
                    <p className="text-sm">Found {analysisResult.events_found} significant event(s). A report has been sent and archived.</p>
                  </div>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      </div>

      {/* Sidebar */}
      <div className="col-span-1 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Video Source</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col space-y-2">
            
            {/* --- Live Sources (Grouped) --- */}
            <Button
              variant="outline"
              onClick={startLocalWebcam}
              disabled={source === "camera" || isConnecting}
              className="w-full relative justify-center" // ✅ Center text
            >
              {isConnecting && !networkUrl ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Camera className="w-4 h-4 absolute left-4" /> // ✅ Position icon
              )}
              <span>{isConnecting && !networkUrl ? "Connecting..." : "Start Local Webcam"}</span>
            </Button>

            <OrDivider />
            
            <div className="space-y-2">
              <div className="relative">
                <Wifi className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
                <Input
                  placeholder="RTSP/HTTP Stream URL..."
                  className="pl-10"
                  value={networkUrl}
                  onChange={(e) => setNetworkUrl(e.target.value)}
                />
              </div>
              <Button
                variant="outline"
                onClick={startNetworkStream}
                disabled={source === "camera" || isConnecting || !networkUrl.trim()}
                className="w-full relative justify-center" // ✅ Center text
              >
                {isConnecting && networkUrl ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Wifi className="w-4 h-4 absolute left-4" /> // ✅ Position icon
                )}
                <span>{isConnecting && networkUrl ? "Connecting..." : "Connect Network Stream"}</span>
              </Button>
            </div>

            <OrDivider />

            {/* --- File Upload Source --- */}
            <Button variant="outline" asChild className="relative">
              <label className="cursor-pointer flex items-center justify-center w-full">
                <Upload className="w-4 h-4 absolute left-4" /> {/* ✅ Position icon */}
                <span>Upload Video</span>
                <input
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={handleFileUpload}
                  ref={fileInputRef}
                />
              </label>
            </Button>

            {/* --- Active Session Controls --- */}
            {source === "camera" && (
              <div className="pt-2 space-y-2 border-t mt-2">
                <Button variant="destructive" onClick={stopCamera} className="w-full">
                  Stop Camera
                </Button>
                <Button
                  variant="outline"
                  onClick={generateCameraReport}
                  disabled={loading}
                  className="border-tech-glow text-tech-glow hover:bg-tech-glow hover:text-background w-full"
                >
                  {loading ? "Generating..." : "Generate Report"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {alerts.length === 0 ? (
              <p className="text-gray-400">No alerts yet</p>
            ) : (
              alerts.map((alert, idx) => (
                <div
                  key={idx}
                  className={`p-2 rounded-md ${
                    alert.type === "warning"
                      ? "bg-yellow-900 text-yellow-200"
                      : alert.type === "error"
                      ? "bg-red-900 text-red-200"
                      : "bg-green-900 text-green-200"
                  }`}
                >
                  <p className="text-sm">{alert.message}</p>
                  <p className="text-xs opacity-70">{alert.timestamp}</p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
// http://192.168.1.6:8080/video
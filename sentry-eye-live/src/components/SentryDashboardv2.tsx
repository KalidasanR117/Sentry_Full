"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import axios from "axios";
import { 
    Play, Pause, Upload, Camera, BarChart3, Shield, Wifi, 
    Loader2, CheckCircle2, AlertTriangle, Power, FileText 
} from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from "sonner";

const API_URL = import.meta.env.VITE_REACT_APP_API_URL || "http://127.0.0.1:5000";
type VideoSource = "none" | "camera" | "upload";

const mockAnalyticsData = [
    { name: '12:00', events: 0 }, { name: '13:00', events: 1 },
    { name: '14:00', events: 0 }, { name: '15:00', events: 3 },
    { name: '16:00', events: 2 }, { name: '17:00', events: 5 },
    { name: '18:00', events: 1 },
];

export const SentryDashboardModern = () => {
    const [source, setSource] = useState<VideoSource>("none");
    const [isPlaying, setIsPlaying] = useState(false);
    const [uploadedFile, setUploadedFile] = useState<File | null>(null);
    const [analysisResult, setAnalysisResult] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [networkUrl, setNetworkUrl] = useState<string>("");
    const videoRef = useRef<HTMLVideoElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const fetchAlerts = async () => {
            try {
                const res = await axios.get(`${API_URL}/api/alerts`);
                setAlerts(res.data);
            } catch (err) {
                console.error("Failed to fetch alerts:", err);
            }
        };
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 5000);
        return () => clearInterval(interval);
    }, []);

    const startLocalWebcam = async () => {
        setIsConnecting(true);
        try {
            await axios.post(`${API_URL}/api/start_camera`, { source: 0 });
            setSource("camera");
            setVideoUrl(`${API_URL}/api/video_feed?timestamp=${new Date().getTime()}`);
            toast.success("Local webcam connected and analysis started.");
        } catch (err: any) {
            toast.error("Failed to start webcam", { description: err.response?.data?.error || "Is it connected and not in use by another app?" });
        } finally {
            setIsConnecting(false);
        }
    };

    const startNetworkStream = async () => {
        if (!networkUrl.trim()) return toast.warning("Please enter a network stream URL.");
        setIsConnecting(true);
        try {
            await axios.post(`${API_URL}/api/start_camera`, { source: networkUrl });
            setSource("camera");
            setVideoUrl(`${API_URL}/api/video_feed?timestamp=${new Date().getTime()}`);
            toast.success("Network stream connected and analysis started.");
        } catch (err: any) {
            toast.error("Failed to connect to stream", { description: err.response?.data?.error || "Please check the URL and your network connection." });
        } finally {
            setIsConnecting(false);
        }
    };

    const stopCamera = async () => {
        setIsConnecting(false);
        await axios.post(`${API_URL}/api/stop_camera`);
        setSource("none");
        setVideoUrl(null);
        toast.info("Camera session has been stopped.");
    };
    
    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setUploadedFile(file);
            setSource("upload");
            setAnalysisResult(null);
            const url = URL.createObjectURL(file);
            setVideoUrl(url);
        }
    };

    const analyzeVideo = async () => {
        if (!uploadedFile) return;
        setLoading(true);
        setAnalysisResult(null);
        try {
            const formData = new FormData();
            formData.append("file", uploadedFile);
            const res = await fetch(`${API_URL}/api/process-video`, { method: "POST", body: formData });
            const data = await res.json();
            if (data.error) throw new Error(data.error);
            setAnalysisResult(data);
            toast.success("Video analysis complete.", { description: `Found ${data.events_found} significant event(s).`});
        } catch (error: any) {
            setAnalysisResult({ error: error.message || "An unexpected error occurred." });
            toast.error("Analysis Failed", { description: error.message || "Please check the console for more details."});
        } finally {
            setLoading(false);
        }
    };

    const generateCameraReport = async () => {
        setLoading(true);
        try {
            const res = await axios.post(`${API_URL}/api/generate-camera-report`);
            toast.success("Report generated successfully.", { description: res.data.status });
        } catch (err: any) {
            toast.error("Failed to generate report.", { description: err.response?.data?.status || "Please try again."});
        } finally {
            setLoading(false);
        }
    };

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1, delayChildren: 0.2 }
        }
    };
    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: { y: 0, opacity: 1, transition: { type: 'spring', stiffness: 100 } }
    };

    return (
        <>
            <style>{`
                @keyframes soft-glow {
                    0% { box-shadow: 0 0 4px #2dd4bf; }
                    50% { box-shadow: 0 0 12px #2dd4bf, 0 0 6px #2dd4bf; }
                    100% { box-shadow: 0 0 4px #2dd4bf; }
                }
                .status-badge-glow {
                    animation: soft-glow 2.5s ease-in-out infinite;
                }
            `}</style>
            <div className="bg-gray-900 text-gray-200 min-h-screen p-4 flex flex-col font-sans">
                <motion.header 
                    className="flex items-center justify-between mb-4 px-2"
                    initial={{ y: -50, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                >
                    <div className="flex items-center gap-4">
                        <Shield className="w-10 h-10 text-amber-400" />
                        <div>
                            <h1 className="text-2xl font-bold text-white">Sentry AI</h1>
                            <p className="text-sm text-gray-400">Intelligent Surveillance Dashboard</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <Badge variant="outline" className="border-teal-400/50 text-teal-300 bg-teal-900/30 status-badge-glow">
                            <div className="w-2 h-2 bg-teal-400 rounded-full mr-2" />
                            System Active
                        </Badge>
                        <Button variant="outline" className="text-gray-300 border-gray-700 hover:bg-gray-800 hover:text-white transition-colors" onClick={() => (window.location.href = "/reports")}>
                            <BarChart3 className="w-4 h-4 mr-2" />
                            View Past Reports
                        </Button>
                    </div>
                </motion.header>

                <motion.main 
                    className="flex-grow grid grid-cols-12 gap-4"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    <motion.aside className="col-span-3 flex flex-col gap-4" variants={itemVariants}>
                        <Card className="bg-gray-800/50 border-gray-700">
                            <CardHeader><CardTitle className="text-white">Source Selection</CardTitle></CardHeader>
                            <CardContent className="flex flex-col gap-3">
                                <p className="text-xs text-gray-400 uppercase font-semibold">Live Sources</p>
                                <Button variant="outline" onClick={startLocalWebcam} disabled={source === 'camera' || isConnecting} className="w-full justify-start gap-2 text-gray-300 border-gray-700 hover:bg-gray-700/50 hover:text-white">
                                    {isConnecting && !networkUrl ? <Loader2 className="w-4 h-4 animate-spin" /> : <Camera className="w-4 h-4" />}
                                    {isConnecting && !networkUrl ? "Connecting..." : "Start Local Webcam"}
                                </Button>
                                <div className="space-y-2">
                                    <Input type="text" placeholder="RTSP/HTTP Stream URL..." value={networkUrl} onChange={e => setNetworkUrl(e.target.value)} className="bg-gray-900 border-gray-600 text-gray-300 placeholder:text-gray-500" />
                                    <Button variant="outline" onClick={startNetworkStream} disabled={source === 'camera' || isConnecting || !networkUrl} className="w-full justify-start gap-2 text-gray-300 border-gray-700 hover:bg-gray-700/50 hover:text-white">
                                        {isConnecting && networkUrl ? <Loader2 className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />}
                                        {isConnecting && networkUrl ? "Connecting..." : "Connect Network Stream"}
                                    </Button>
                                </div>
                                <p className="text-xs text-gray-400 uppercase font-semibold pt-2">Recorded Video</p>
                                <Button variant="outline" asChild className="w-full justify-start gap-2 text-gray-300 border-gray-700 hover:bg-gray-700/50 hover:text-white">
                                    <label className="cursor-pointer"><Upload className="w-4 h-4" /> Upload Video File <input type="file" className="hidden" ref={fileInputRef} onChange={handleFileUpload} /></label>
                                </Button>
                            </CardContent>
                        </Card>

                        {source === 'camera' && (
                            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                                <Card className="bg-gray-800/50 border-gray-700">
                                    <CardHeader><CardTitle className="text-white">Session Controls</CardTitle></CardHeader>
                                    <CardContent className="flex flex-col gap-3">
                                        <Button variant="destructive" onClick={stopCamera} className="w-full justify-start gap-2">
                                            <Power className="w-4 h-4" /> Stop Camera
                                        </Button>
                                        <Button variant="outline" onClick={generateCameraReport} disabled={loading} className="w-full justify-start gap-2 text-gray-300 border-gray-700 hover:bg-gray-700/50 hover:text-white">
                                            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                                            {loading ? "Generating..." : "Generate Report"}
                                        </Button>
                                    </CardContent>
                                </Card>
                            </motion.div>
                        )}
                    </motion.aside>

                    <motion.section className="col-span-6 flex flex-col" variants={itemVariants}>
                        <Card className="bg-gray-800/50 border-gray-700 flex-grow flex flex-col hover:border-amber-400/50 transition-colors">
                            <CardHeader>
                                <CardTitle className="text-white flex justify-between items-center">
                                    <span>Live Feed</span>
                                    {source === 'camera' && <Badge variant="outline" className="border-green-400/50 text-green-300 bg-green-900/30">● Live Analysis</Badge>}
                                    {source === 'upload' && <Badge variant="secondary">{uploadedFile?.name}</Badge>}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="flex-grow flex items-center justify-center bg-black rounded-b-lg p-1">
                                 {videoUrl ? (
                                    source === "camera" ? (
                                        <img src={videoUrl} alt="Camera feed" className="max-h-full max-w-full object-contain" />
                                    ) : (
                                        <video ref={videoRef} src={videoUrl} controls autoPlay className="max-h-full max-w-full object-contain" />
                                    )
                                ) : (
                                    <div className="text-center text-gray-500">
                                        <Camera className="w-16 h-16 mx-auto mb-2" />
                                        <p>No Video Source Selected</p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                        {source === 'upload' && (
                             <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center justify-end gap-2 p-4 bg-gray-800/50 border-t-0 border-x border-b border-gray-700 rounded-b-lg">
                                 <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()} className="text-gray-300 border-gray-700 hover:bg-gray-700/50 hover:text-white">
                                     <Upload className="w-4 h-4 mr-2" />
                                     Change Video
                                 </Button>
                                 <Button onClick={analyzeVideo} disabled={!uploadedFile || loading} className="bg-amber-500 hover:bg-amber-600 text-black">
                                     {loading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Analyzing...</> : "Analyze Video"}
                                 </Button>
                             </motion.div>
                        )}
                        {analysisResult && (
                             <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="p-4 mt-4 bg-gray-800/50 border border-gray-700 rounded-lg">
                                 <h3 className="text-lg font-bold mb-2 text-white">Analysis Result</h3>
                                 {analysisResult.error ? (
                                     <div className="flex items-start gap-3 p-3 bg-red-900/50 text-red-300 rounded-md">
                                         <AlertTriangle className="w-6 h-6 flex-shrink-0 mt-1" />
                                         <div>
                                             <p className="font-semibold">An Error Occurred</p>
                                             <p className="text-sm">{analysisResult.error}</p>
                                         </div>
                                     </div>
                                 ) : (
                                     <div className="flex items-start gap-3 p-3 bg-green-900/50 text-green-300 rounded-md">
                                         <CheckCircle2 className="w-6 h-6 flex-shrink-0 mt-1" />
                                         <div>
                                             <p className="font-semibold">{analysisResult.status}</p>
                                             <p className="text-sm">Found {analysisResult.events_found} significant event(s). A report has been sent and archived.</p>
                                         </div>
                                     </div>
                                 )}
                             </motion.div>
                         )}
                    </motion.section>

                    <motion.aside className="col-span-3 flex flex-col gap-4" variants={itemVariants}>
                        <Card className="bg-gray-800/50 border-gray-700 flex-grow flex flex-col">
                            <CardHeader>
                                <CardTitle className="text-white">Recent Alerts</CardTitle>
                                <CardDescription>Live feed of detected events.</CardDescription>
                            </CardHeader>
                            <CardContent className="flex-grow space-y-2 overflow-y-auto pr-2">
                                <AnimatePresence>
                                    {alerts.length === 0 ? (
                                        <motion.p 
                                            className="text-gray-500 text-sm text-center pt-8"
                                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                                        >
                                            No alerts yet.
                                        </motion.p>
                                    ) : (
                                        alerts.map((alert, idx) => (
                                            <motion.div 
                                                key={alert.timestamp + idx} // More robust key
                                                layout
                                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                                exit={{ opacity: 0, scale: 0.95 }}
                                                transition={{ duration: 0.3, ease: 'easeOut' }}
                                                className={`p-2 rounded-md text-sm ${alert.type === "warning" ? "bg-amber-900/50 text-amber-300" : "bg-red-900/50 text-red-300"}`}
                                            >
                                                <p className="font-semibold">{alert.message}</p>
                                                <p className="text-xs text-gray-400">{alert.timestamp}</p>
                                            </motion.div>
                                        ))
                                    )}
                                </AnimatePresence>
                            </CardContent>
                        </Card>
                        <Card className="bg-gray-800/50 border-gray-700">
                            <CardHeader>
                                <CardTitle className="text-white">System Analytics</CardTitle>
                                <CardDescription>Event frequency over time.</CardDescription>
                            </CardHeader>
                            <CardContent className="h-40">
                                 <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={mockAnalyticsData} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
                                        <defs>
                                            <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#FBBF24" stopOpacity={0.8}/>
                                                <stop offset="95%" stopColor="#FBBF24" stopOpacity={0}/>
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
                                        <XAxis dataKey="name" stroke="#A0AEC0" fontSize={12} />
                                        <YAxis stroke="#A0AEC0" fontSize={12}/>
                                        <Tooltip contentStyle={{ backgroundColor: '#1A202C', border: '1px solid #4A5568' }} />
                                        <Area type="monotone" dataKey="events" stroke="#FBBF24" strokeWidth={2} fillOpacity={1} fill="url(#colorEvents)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </CardContent>
                        </Card>
                    </motion.aside>
                </motion.main>
            </div>
        </>
    );
};


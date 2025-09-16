"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { 
  ArrowLeft, Search, Filter, Download, Clock, Upload, Camera, Trash2, Loader2 
} from "lucide-react";
import axios from "axios";
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from "sonner";

const API_URL = import.meta.env.VITE_REACT_APP_API_URL || "http://127.0.0.1:5000";

type Report = {
  id: number;
  timestamp: string;
  report_type: 'upload' | 'camera';
  summary: string;
  pdf_filename: string;
};

const Reports = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");
  const [reportToDelete, setReportToDelete] = useState<Report | null>(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        const res = await axios.get(`${API_URL}/api/reports`);
        setReports(res.data);
      } catch (err) {
        console.error("Failed to fetch reports:", err);
        toast.error("Failed to fetch reports from the server.");
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);
  
  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      const matchesSearch = report.summary.toLowerCase().includes(searchTerm.toLowerCase()) || report.timestamp.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = typeFilter === 'all' || report.report_type === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [reports, searchTerm, typeFilter]);
  
  const handleDownload = (filename: string) => {
    const link = document.createElement('a');
    link.href = `${API_URL}/api/download-report/${filename}`;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDelete = (report: Report) => {
    setReportToDelete(report);
  };

  const confirmDelete = async () => {
    if (!reportToDelete) return;
    try {
      await axios.delete(`${API_URL}/api/reports/${reportToDelete.id}`);
      setReports(reports.filter(r => r.id !== reportToDelete.id));
      toast.success(`Report #${reportToDelete.id} has been deleted.`);
    } catch (err) {
      console.error("Failed to delete report:", err);
      toast.error("Could not delete the report. Please try again.");
    } finally {
      setReportToDelete(null);
    }
  };
  
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.07 }
        }
    };
    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: { y: 0, opacity: 1, transition: { type: 'spring', stiffness: 100 } }
    };

  return (
    <>
      <div className="bg-gray-900 text-gray-200 min-h-screen p-6 font-sans">
        <div className="max-w-5xl mx-auto space-y-6">
          <motion.div 
              className="flex items-center justify-between"
              initial={{ y: -50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
          >
            <div className="flex items-center gap-4">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => window.location.href = '/'}
                className="text-gray-300 border-gray-700 hover:bg-gray-800 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Dashboard
              </Button>
              <div>
                <h1 className="text-3xl font-bold text-white">Past Reports</h1>
                <p className="text-gray-400">View and manage the surveillance event archive</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="border-amber-400/50 text-amber-300 bg-amber-900/30">
                {filteredReports.length} Reports Found
              </Badge>
            </div>
          </motion.div>

          <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}>
              <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                      <CardTitle className="flex items-center gap-2 text-white">
                          <Filter className="w-5 h-5" />
                          Filter & Search
                      </CardTitle>
                  </CardHeader>
                  <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="relative md:col-span-1">
                          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-500" />
                          <Input 
                              placeholder="Search summaries or timestamps..."
                              className="pl-10 bg-gray-900 border-gray-600 text-gray-300 placeholder:text-gray-500"
                              value={searchTerm}
                              onChange={(e) => setSearchTerm(e.target.value)}
                          />
                      </div>
                      
                      <Select value={typeFilter} onValueChange={setTypeFilter}>
                          <SelectTrigger className="bg-gray-900 border-gray-600 text-gray-300">
                              <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-gray-800 border-gray-700 text-gray-200">
                              <SelectItem value="all">All Source Types</SelectItem>
                              <SelectItem value="upload">Uploaded Video</SelectItem>
                              <SelectItem value="camera">Live Camera</SelectItem>
                          </SelectContent>
                      </Select>
                      </div>
                  </CardContent>
              </Card>
          </motion.div>

          <div className="space-y-4">
            {loading ? (
              <div className="flex justify-center items-center py-16">
                  <Loader2 className="w-8 h-8 animate-spin text-amber-400" />
              </div>
            ) : (
               <AnimatePresence>
                  {filteredReports.length === 0 ? (
                      <motion.p 
                          className="text-gray-500 text-center py-16"
                          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      >
                          No reports match the current filters.
                      </motion.p>
                  ) : (
                      <motion.div
                          className="space-y-4"
                          variants={containerVariants}
                          initial="hidden"
                          animate="visible"
                      >
                      {filteredReports.map((report) => (
                          <motion.div key={report.id} variants={itemVariants}>
                              <Card className="bg-gray-800/50 border-gray-700 hover:border-amber-400/50 transition-colors">
                                  <CardContent className="p-6">
                                      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                                      <div className="flex items-start gap-4 flex-grow">
                                          <div className="mt-1">
                                              {report.report_type === 'camera' ? (
                                                  <Camera className="w-6 h-6 text-red-400" />
                                              ) : (
                                                  <Upload className="w-6 h-6 text-sky-400" />
                                              )}
                                          </div>
                                          <div className="flex-grow space-y-2">
                                              <h3 className="text-lg font-semibold text-white">
                                                  {report.report_type === 'upload' ? 'Uploaded Video Analysis' : 'Live Camera Session Report'}
                                              </h3>
                                              <div className="flex items-center gap-2 text-sm text-gray-400">
                                                  <Clock className="w-4 h-4" />
                                                  {new Date(report.timestamp).toLocaleString()}
                                              </div>
                                              <p className="text-sm text-gray-300 pt-2 leading-relaxed">
                                                  {report.summary}
                                              </p>
                                          </div>
                                      </div>
                                      <div className="flex items-center gap-2 flex-shrink-0 self-start md:self-center">
                                          <Button 
                                              variant="outline" 
                                              size="sm"
                                              className="text-gray-300 border-gray-700 hover:bg-gray-700/50 hover:text-white"
                                              onClick={() => handleDownload(report.pdf_filename)}
                                          >
                                              <Download className="w-4 h-4 mr-2" />
                                              PDF
                                          </Button>
                                          <Button 
                                              variant="destructive" 
                                              size="sm"
                                              onClick={() => handleDelete(report)}
                                          >
                                              <Trash2 className="w-4 h-4 mr-2" />
                                              Delete
                                          </Button>
                                      </div>
                                      </div>
                                  </CardContent>
                              </Card>
                          </motion.div>
                      ))}
                      </motion.div>
                  )}
              </AnimatePresence>
            )}
          </div>
        </div>
      </div>

      <AlertDialog open={!!reportToDelete} onOpenChange={() => setReportToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete Report #{reportToDelete?.id}
              and remove its PDF file from the server.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete}>Confirm Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
};

export default Reports;



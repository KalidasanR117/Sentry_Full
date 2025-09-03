"use client";

import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  ArrowLeft, 
  Search, 
  Filter, 
  Download,
  Clock,
  Upload,
  Camera,
  Trash2 // ✅ NEW: Import the delete icon
} from "lucide-react";
import axios from "axios";

// Define a type that matches the data from your backend API
type Report = {
  id: number;
  timestamp: string;
  report_type: 'upload' | 'camera';
  summary: string;
  pdf_filename: string;
};

const Reports = () => {
  // State for real data, loading, and filters
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  // Fetch data from the backend when the component loads
  useEffect(() => {
    const fetchReports = async () => {
      try {
        setLoading(true);
        const res = await axios.get("http://127.0.0.1:5000/api/reports");
        setReports(res.data);
      } catch (err) {
        console.error("Failed to fetch reports:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);
  
  // Memoized filtering logic
  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      const matchesSearch = report.summary.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesType = typeFilter === 'all' || report.report_type === typeFilter;
      return matchesSearch && matchesType;
    });
  }, [reports, searchTerm, typeFilter]);
  
  // Handler to download the PDF
  const handleDownload = (filename: string) => {
    const link = document.createElement('a');
    link.href = `http://127.0.0.1:5000/api/download-report/${filename}`;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // ✅ NEW: Handler to delete a report
  const handleDelete = async (reportId: number) => {
    // Ask for confirmation before deleting
    if (!window.confirm("Are you sure you want to permanently delete this report?")) {
      return;
    }
    try {
      await axios.delete(`http://127.0.0.1:5000/api/reports/${reportId}`);
      // Remove the deleted report from the state to update the UI instantly
      setReports(reports.filter(report => report.id !== reportId));
    } catch (err) {
      console.error("Failed to delete report:", err);
      alert("Could not delete the report. Please try again.");
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => window.location.href = '/'}
              className="border-tech-glow text-tech-glow hover:bg-tech-glow hover:text-background"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Dashboard
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-foreground">Surveillance Reports</h1>
              <p className="text-muted-foreground">View and analyze past surveillance events</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-tech-glow text-tech-glow">
              {filteredReports.length} Reports Found
            </Badge>
          </div>
        </div>

        {/* Filters */}
        <Card className="bg-gradient-card shadow-card border-border">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-foreground">
              <Filter className="w-5 h-5" />
              Filters & Search
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="relative md:col-span-1">
                <Search className="w-4 h-4 absolute left-3 top-3 text-muted-foreground" />
                <Input 
                  placeholder="Search summaries..."
                  className="pl-10 bg-input border-border text-foreground"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="bg-input border-border text-foreground">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-popover border-border">
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="upload">Uploaded Video</SelectItem>
                  <SelectItem value="camera">Live Camera</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Reports List */}
        <div className="space-y-4">
          {loading ? (
            <p>Loading reports...</p>
          ) : filteredReports.length === 0 ? (
            <p className="text-muted-foreground text-center">No reports match the current filters.</p>
          ) : (
            filteredReports.map((report) => (
              <Card key={report.id} className="bg-gradient-card shadow-card border-border hover:border-tech-glow transition-colors">
                <CardContent className="p-6">
                  <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex-grow space-y-2">
                      <div className="flex items-center gap-3">
                        <h3 className="text-lg font-semibold text-foreground">
                          {report.report_type === 'upload' ? 'Uploaded Video Analysis' : 'Live Camera Session Report'}
                        </h3>
                        <Badge variant={report.report_type === 'camera' ? 'destructive' : 'default'}>
                          {report.report_type === 'camera' ? (
                            <Camera className="w-4 h-4 mr-2" />
                          ) : (
                            <Upload className="w-4 h-4 mr-2" />
                          )}
                          {report.report_type}
                        </Badge>
                      </div>
                      
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        {new Date(report.timestamp).toLocaleString()}
                      </div>
                      
                      <p className="text-sm text-muted-foreground pt-2">
                        {report.summary}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Button 
                        variant="outline" 
                        size="sm"
                        className="border-tech-glow text-tech-glow hover:bg-tech-glow hover:text-background"
                        onClick={() => handleDownload(report.pdf_filename)}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download PDF
                      </Button>
                      {/* ✅ NEW: Delete Button */}
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={() => handleDelete(report.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Reports;
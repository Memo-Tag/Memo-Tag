import { Button } from "@/components/ui/button";
import { Download, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import jsPDF from "jspdf";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: string[];
  searchResults?: Array<{
    title: string;
    url: string;
    snippet: string;
    date?: string;
  }>;
  createdAt?: string;
}

interface ExportConversationPDFProps {
  conversationTitle: string;
  messages: Message[];
  userName?: string;
}

export function ExportConversationPDF({
  conversationTitle,
  messages,
  userName = "User",
}: ExportConversationPDFProps) {
  const [isExporting, setIsExporting] = useState(false);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return new Date().toLocaleDateString();
    const date = new Date(dateStr);
    return date.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const wrapText = (text: string, maxWidth: number, fontSize: number): string[] => {
    const doc = new jsPDF();
    doc.setFontSize(fontSize);
    return doc.splitTextToSize(text, maxWidth);
  };

  const exportToPDF = async () => {
    if (messages.length === 0) {
      toast.error("No messages to export");
      return;
    }

    setIsExporting(true);
    try {
      const doc = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      const pageWidth = doc.internal.pageSize.getWidth();
      const pageHeight = doc.internal.pageSize.getHeight();
      const margin = 15;
      const maxWidth = pageWidth - 2 * margin;
      let yPosition = margin;

      // Helper function to check if we need a new page
      const checkNewPage = (requiredSpace: number) => {
        if (yPosition + requiredSpace > pageHeight - margin - 10) {
          doc.addPage();
          yPosition = margin;
          return true;
        }
        return false;
      };

      // Clean professional header
      doc.setFillColor(52, 73, 94); // Professional dark blue-gray
      doc.rect(0, 0, pageWidth, 35, "F");
      
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(18);
      doc.setFont("helvetica", "bold");
      doc.text("MedChat - Medical Consultation", margin, 15);
      
      doc.setFontSize(11);
      doc.setFont("helvetica", "normal");
      const titleText = conversationTitle || "Conversation";
      doc.text(titleText.substring(0, 80), margin, 23);
      doc.text(`Exported: ${formatDate()}`, margin, 29);

      yPosition = 42;

      // Process ALL messages
      for (let index = 0; index < messages.length; index++) {
        const message = messages[index];
        const isUser = message.role === "user";
        
        // Check space for message header
        checkNewPage(15);

        // Message header with clean design
        if (isUser) {
          doc.setFillColor(240, 248, 255); // Very light blue
        } else {
          doc.setFillColor(248, 250, 252); // Very light gray
        }
        doc.roundedRect(margin, yPosition, maxWidth, 8, 2, 2, "F");
        
        // Sender name
        doc.setFontSize(10);
        doc.setFont("helvetica", "bold");
        if (isUser) {
          doc.setTextColor(41, 98, 255); // Blue for user
        } else {
          doc.setTextColor(34, 139, 34); // Green for AI
        }
        const senderName = isUser ? userName : "MedChat AI";
        doc.text(senderName, margin + 3, yPosition + 5.5);

        // Timestamp
        if (message.createdAt) {
          doc.setFont("helvetica", "normal");
          doc.setFontSize(8);
          doc.setTextColor(120, 120, 120);
          const timeText = formatDate(message.createdAt);
          const timeWidth = doc.getTextWidth(timeText);
          doc.text(timeText, pageWidth - margin - timeWidth - 3, yPosition + 5.5);
        }

        yPosition += 10;

        // Message content with bold text support
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(10);
        
        // Parse content for bold markers (**text**)
        const content = message.content;
        const lines = content.split('\n');
        
        for (const line of lines) {
          if (!line.trim()) {
            checkNewPage(5);
            yPosition += 5;
            continue;
          }
          
          // Process line with bold support
          // Split by bold markers to get parts
          const boldRegex = /\*\*(.*?)\*\*/g;
          const parts: Array<{text: string, bold: boolean}> = [];
          let lastIndex = 0;
          let match;
          
          // Find all bold sections
          while ((match = boldRegex.exec(line)) !== null) {
            // Add text before bold
            if (match.index > lastIndex) {
              parts.push({text: line.substring(lastIndex, match.index), bold: false});
            }
            // Add bold text
            parts.push({text: match[1], bold: true});
            lastIndex = match.index + match[0].length;
          }
          // Add remaining text
          if (lastIndex < line.length) {
            parts.push({text: line.substring(lastIndex), bold: false});
          }
          
          // If no bold markers found, treat entire line as normal
          if (parts.length === 0) {
            parts.push({text: line, bold: false});
          }
          
          // Now render the parts with proper bold handling
          let currentLineText = '';
          let currentLineParts: Array<{text: string, bold: boolean}> = [];
          
          for (const part of parts) {
            const testText = currentLineText + part.text;
            doc.setFont("helvetica", "normal");
            const testWidth = doc.getTextWidth(testText);
            
            if (testWidth > maxWidth - 6) {
              // Need to wrap - first render current line
              if (currentLineParts.length > 0) {
                checkNewPage(6);
                let xPos = margin + 3;
                for (const p of currentLineParts) {
                  doc.setFont("helvetica", p.bold ? "bold" : "normal");
                  doc.text(p.text, xPos, yPosition);
                  xPos += doc.getTextWidth(p.text);
                }
                yPosition += 6;
              }
              
              // Start new line with current part
              currentLineText = part.text;
              currentLineParts = [part];
            } else {
              // Add to current line
              currentLineText = testText;
              currentLineParts.push(part);
            }
          }
          
          // Render remaining parts
          if (currentLineParts.length > 0) {
            checkNewPage(6);
            let xPos = margin + 3;
            for (const p of currentLineParts) {
              doc.setFont("helvetica", p.bold ? "bold" : "normal");
              doc.text(p.text, xPos, yPosition);
              xPos += doc.getTextWidth(p.text);
            }
            yPosition += 6;
          }
        }

        yPosition += 3;

        // References (changed from Sources)
        if (message.searchResults && message.searchResults.length > 0) {
          checkNewPage(10);
          
          doc.setFontSize(9);
          doc.setFont("helvetica", "bold");
          doc.setTextColor(70, 70, 70);
          doc.text("References:", margin + 3, yPosition);
          yPosition += 6;

          for (let idx = 0; idx < message.searchResults.length; idx++) {
            const result = message.searchResults[idx];
            checkNewPage(12);
            
            // Reference title (bold, black)
            doc.setFont("helvetica", "bold");
            doc.setFontSize(9);
            doc.setTextColor(0, 0, 0);
            const titleText = `${idx + 1}. ${result.title}`;
            const titleLines = wrapText(titleText, maxWidth - 10, 9);
            for (const titleLine of titleLines) {
              checkNewPage(5);
              doc.text(titleLine, margin + 6, yPosition);
              yPosition += 5;
            }

            // URL (clickable link, blue)
            doc.setFont("helvetica", "normal");
            doc.setFontSize(8);
            doc.setTextColor(41, 98, 255);
            
            checkNewPage(4);
            doc.textWithLink(result.url, margin + 6, yPosition, { url: result.url });
            yPosition += 5;
          }
          yPosition += 3;
        }

        // Add spacing between messages
        yPosition += 5;
      }

      // Footer on all pages
      const pageCount = doc.internal.pages.length - 1;
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        
        doc.setFontSize(8);
        doc.setTextColor(150, 150, 150);
        doc.setFont("helvetica", "normal");
        
        const footerText = `Page ${i}/${pageCount} | MedChat Medical AI | ${formatDate().split(",")[0]}`;
        const footerWidth = doc.getTextWidth(footerText);
        doc.text(footerText, (pageWidth - footerWidth) / 2, pageHeight - 8);
      }

      // Generate filename
      const sanitizedTitle = conversationTitle
        .replace(/[^a-z0-9]/gi, "_")
        .substring(0, 50);
      const filename = `MedChat_${sanitizedTitle}_${new Date().toISOString().split("T")[0]}.pdf`;

      // Save PDF
      doc.save(filename);
      toast.success("Conversation exported successfully!");
    } catch (error) {
      console.error("Failed to export PDF:", error);
      toast.error("Failed to export conversation. Please try again.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={exportToPDF}
      disabled={isExporting || messages.length === 0}
      className="w-full justify-start gap-2"
      title="Export conversation as PDF"
    >
      {isExporting ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <Download className="w-4 h-4" />
      )}
      <span>{isExporting ? "Exporting..." : "Export to PDF"}</span>
    </Button>
  );
}

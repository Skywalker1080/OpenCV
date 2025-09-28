from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, Response, make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os
from datetime import datetime
import os
import subprocess
import sys

# Add the project root to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.dbsql import get_all_violations, update_number_plate, delete_violation, delete_all_violations, export_violations_to_csv, get_violation_by_id

app = Flask(__name__)
app.secret_key = "your_secret_key"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Check if it's a webcam detection request
        if "webcam_detection" in request.form:
            duration = int(request.form.get("duration", 30))
            
            # Run webcam detection
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join("app", "realtime_webcam.py"), 
                     "--duration", str(duration), "--no-display"],
                    capture_output=True, text=True, timeout=duration + 30,  # Duration + buffer
                    cwd=os.getcwd()
                )
                
                if result.returncode == 0:
                    # Extract violation count from output
                    output_lines = result.stdout.strip().split('\n')
                    violation_msg = f"Webcam detection completed for {duration} seconds!"
                    for line in output_lines:
                        if "Total violations detected:" in line:
                            violation_msg = f"Webcam detection completed! {line}"
                            break
                    flash(violation_msg)
                else:
                    flash(f"Webcam detection failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                flash("Webcam detection timed out.")
            except Exception as e:
                flash(f"Error during webcam detection: {str(e)}")
                
            return redirect(url_for("index"))
        
        # Handle video file upload
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file:
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            
            # Run your detection backend (realtime.py) on the uploaded file
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join("app", "realtime.py"), filepath, "--no-display"],
                    capture_output=True, text=True, timeout=300,  # 5 minute timeout
                    cwd=os.getcwd()  # Set working directory to project root
                )
                
                if result.returncode == 0:
                    # Extract violation count from output
                    output_lines = result.stdout.strip().split('\n')
                    violation_msg = "Video detection completed!"
                    for line in output_lines:
                        if "Total violations detected:" in line:
                            violation_msg = f"Video detection completed! {line}"
                            break
                    flash(violation_msg)
                else:
                    flash(f"Video detection failed: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                flash("Detection timed out. Please try with a smaller video file.")
            except Exception as e:
                flash(f"Error during detection: {str(e)}")
                
            return redirect(url_for("index"))
    return render_template("index.html")

@app.route("/admin")
def admin_dashboard():
    """Admin dashboard to view all violations"""
    try:
        violations = get_all_violations()
        return render_template("admin.html", violations=violations)
    except Exception as e:
        flash(f"Error loading violations: {str(e)}")
        return redirect(url_for("index"))

@app.route('/image/<path:filepath>')
def serve_image_file(filepath):
    """Serve images from project directory"""
    try:
        # Handle path without separator (e.g., "cropsannotated_1756015946134.jpg")
        if filepath.startswith('crops') and not filepath.startswith('crops/') and not filepath.startswith('crops\\'):
            # Missing separator - extract filename after "crops"
            filename = filepath[5:]  # Remove "crops" prefix
            directory = os.path.join(os.getcwd(), 'crops')
            return send_from_directory(directory, filename)
        elif filepath.startswith('annotated_frames') and not filepath.startswith('annotated_frames/') and not filepath.startswith('annotated_frames\\'):
            # Missing separator - extract filename after "annotated_frames"
            filename = filepath[15:]  # Remove "annotated_frames" prefix
            directory = os.path.join(os.getcwd(), 'annotated_frames')
            return send_from_directory(directory, filename)
        # Handle normal paths with separators
        elif filepath.startswith('crops\\') or filepath.startswith('crops/'):
            filename = filepath.split('\\')[-1] if '\\' in filepath else filepath.split('/')[-1]
            directory = os.path.join(os.getcwd(), 'crops')
            return send_from_directory(directory, filename)
        elif filepath.startswith('annotated_frames\\') or filepath.startswith('annotated_frames/'):
            filename = filepath.split('\\')[-1] if '\\' in filepath else filepath.split('/')[-1]
            directory = os.path.join(os.getcwd(), 'annotated_frames')
            return send_from_directory(directory, filename)
        else:
            # Try direct file path
            return send_from_directory(os.getcwd(), filepath)
    except Exception as e:
        print(f"Error serving image {filepath}: {e}")
        return "Image not found", 404

@app.route('/update_number_plate', methods=['POST'])
def update_plate():
    """Update number plate for a violation"""
    try:
        data = request.get_json()
        violation_id = data.get('violation_id')
        number_plate = data.get('number_plate', '').strip()
        
        update_number_plate(violation_id, number_plate)
        return jsonify({'status': 'success', 'message': 'Number plate updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_violation', methods=['POST'])
def delete_violation_route():
    """Delete a violation record"""
    try:
        data = request.get_json()
        violation_id = data.get('violation_id')
        
        if not violation_id:
            return jsonify({'status': 'error', 'message': 'Violation ID is required'}), 400
        
        success = delete_violation(violation_id)
        if success:
            return jsonify({'status': 'success', 'message': 'Violation deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Violation not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/delete_all_violations', methods=['POST'])
def delete_all_violations_route():
    """Delete all violation records"""
    try:
        rows_deleted = delete_all_violations()
        return jsonify({
            'status': 'success', 
            'message': f'Successfully deleted {rows_deleted} violation records'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/export_csv')
def export_csv():
    """Export all violations to CSV file"""
    try:
        csv_data = export_violations_to_csv()
        
        # Create response with CSV data
        response = Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=traffic_violations.csv'
            }
        )
        return response
    except Exception as e:
        flash(f"Error exporting CSV: {str(e)}")
        return redirect(url_for('admin_dashboard'))

@app.route('/generate_challan/<int:violation_id>')
def generate_challan(violation_id):
    """Generate and return a PDF challan for the given violation"""
    try:
        violation = get_violation_by_id(violation_id)
        if not violation:
            return "Violation not found", 404
            
        # Create a file-like buffer to receive PDF data
        buffer = BytesIO()
        
        # Create the PDF object, using the buffer as its "file"
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add title
        p.setFont("Helvetica-Bold", 18)
        p.drawCentredString(300, 750, "E-CHALLAN")
        
        # Add challan ID and date
        p.setFont("Helvetica", 10)
        p.drawRightString(550, 780, f"Challan ID: MTCPHM1801133383")
        p.drawRightString(550, 765, f"Date: {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')} UTC")
        
        # Add violation details
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, 700, "VIOLATION DETAILS")
        p.line(50, 695, 150, 695)
        
        p.setFont("Helvetica", 10)
        y = 670
        details = [
            ("Violation Type:", violation['violation_type']),
            ("Date & Time:", violation['ts_utc'].replace('T', ' ')),
            ("Vehicle Number:", violation['number_plate'] or "Not Available"),
            ("Fine Amount:", f"Rs {violation['fine']}"),
            ("Location:", "City Traffic Police, Pune")
        ]
        
        for label, value in details:
            p.drawString(50, y, f"{label} {value}")
            y -= 25
            
        # Add violation image if available
        if violation['file_path'] and os.path.exists(violation['file_path']):
            try:
                img = ImageReader(violation['file_path'])
                img_width, img_height = img.getSize()
                aspect = img_height / float(img_width)
                display_width = 200
                display_height = display_width * aspect
                
                if y - display_height - 20 < 100:  # Check if we need a new page
                    p.showPage()
                    y = 750
                
                p.drawImage(violation['file_path'], 50, y - display_height - 10, 
                          width=display_width, height=display_height)
                p.drawString(50, y - display_height - 20, "Evidence:")
            except Exception as e:
                print(f"Error adding image to PDF: {e}")
        
        # Add payment instructions
        p.setFont("Helvetica-Bold", 12)
        p.drawString(300, 200, "PAYMENT INSTRUCTIONS")
        p.line(300, 195, 450, 195)
        
        p.setFont("Helvetica", 10)
        p.drawString(300, 170, "1. Pay online at: https://echallan.parivahan.gov.in/")
        p.drawString(300, 150, "2. Visit nearest traffic police station")
        p.drawString(300, 130, "3. Pay via UPI: traffic.police@gov.in")
        
        # Add footer
        p.setFont("Helvetica-Oblique", 8)
        p.drawCentredString(300, 50, "This is a computer generated challan and does not require any signature.")
        
        # Close the PDF object cleanly
        p.showPage()
        p.save()
        
        # File response
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.mimetype = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=challan_{violation_id}.pdf'
        return response
        
    except Exception as e:
        print(f"Error generating challan: {e}")
        return f"Error generating challan: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
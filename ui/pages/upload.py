import streamlit as st
from ui.auth_manager import AuthManager
from processing.ingestion import save_uploaded_file
from processing.parsing import parse_document
from database.database import get_db
from database.crud import create_receipt
from utils.errors import FileProcessingError, ParsingError
import pandas as pd
from datetime import date
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def show_upload_page():
    auth_manager = AuthManager()
    auth_manager.require_login() # Ensure user is logged in

    user_id = auth_manager.get_current_user_id()

    st.title("⬆️ Upload Your Receipts & Bills")
    st.markdown("Upload image files (.jpg, .png), PDFs (.pdf), or text files (.txt).")

    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=["jpg", "jpeg", "png", "pdf", "txt"],
        accept_multiple_files=True,
        help="You can drag and drop files here or click to browse."
    )

    if uploaded_files:
        st.subheader("Processing Uploaded Files...")
        progress_bar = st.progress(0)
        total_files = len(uploaded_files)
        processed_count = 0

        parsed_results = []
        parsing_errors = []

        for i, uploaded_file in enumerate(uploaded_files):
            file_name = uploaded_file.name
            st.write(f"Processing: **{file_name}**")

            # 1. Save the file temporarily (or permanently if desired)
            saved_file_path, original_filename = save_uploaded_file(uploaded_file)

            if saved_file_path:
                try:
                    # 2. Parse the document
                    parsed_data = parse_document(saved_file_path, original_filename)

                    # 3. Save parsed data to database
                    if parsed_data:
                        db_gen = get_db()
                        db = next(db_gen)
                        try:
                            # Use validated data from Pydantic model
                            db_receipt = create_receipt(
                                db=db,
                                owner_id=user_id,
                                vendor_name=parsed_data.vendor_name,
                                transaction_date=parsed_data.transaction_date,
                                amount=parsed_data.amount,
                                currency=parsed_data.currency,
                                category_name=parsed_data.category_name,
                                original_filename=original_filename,
                                parsed_raw_text=parsed_data.parsed_raw_text,
                                billing_period_start=parsed_data.billing_period_start,
                                billing_period_end=parsed_data.billing_period_end
                            )
                            parsed_results.append(db_receipt)
                            st.success(f"Successfully processed and recorded: **{original_filename}** (Vendor: {parsed_data.vendor_name}, Amount: {parsed_data.amount:.2f} {parsed_data.currency})")
                            logger.info(f"File {original_filename} processed and saved to DB.")
                        except Exception as db_err:
                            st.error(f"Failed to save data for {original_filename} to database: {db_err}")
                            parsing_errors.append(f"DB Error for {original_filename}: {db_err}")
                        finally:
                            db.close()
                    else:
                        st.warning(f"Could not extract meaningful data from: **{original_filename}**.")
                        parsing_errors.append(f"No data extracted from {original_filename}.")

                except (FileProcessingError, ParsingError) as e:
                    st.error(f"Error processing **{original_filename}**: {e}")
                    parsing_errors.append(f"Processing Error for {original_filename}: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred while processing **{original_filename}**: {e}")
                    parsing_errors.append(f"Unexpected Error for {original_filename}: {e}")
                finally:
                    # Optional: Clean up saved_file_path if it was just for temporary processing
                    # os.remove(saved_file_path)
                    pass # Keeping files for now as per data/raw_receipts structure

            else:
                st.error(f"Failed to save {file_name} to disk.")
                parsing_errors.append(f"File save error for {file_name}.")

            processed_count += 1
            progress_bar.progress((processed_count / total_files))

        progress_bar.empty() # Remove progress bar after completion

        st.markdown("---")
        st.subheader("Processing Complete!")

        if parsed_results:
            st.success(f"🎉 Successfully processed {len(parsed_results)} out of {total_files} files.")
            if st.button("View Processed Records"):
        # Corrected: Use the correct session state variable and force rerun
                st.session_state["current_main_page"] = "View Records"
                st.rerun()
        else:
            st.warning("No new records were successfully processed.")

        if parsing_errors:
            st.error(f"⚠️ Encountered {len(parsing_errors)} errors during processing. See details below:")
            for error in parsing_errors:
                st.code(error)

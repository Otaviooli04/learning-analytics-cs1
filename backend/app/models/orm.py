from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    number = Column(String)
    statement = Column(Text)
    required_structures = Column(JSON, default=list)
    forbidden_structures = Column(JSON, default=list)
    requires_loop = Column(Boolean, default=False)

    exam = relationship("Exam", back_populates="questions")
    test_cases = relationship("TestCase", back_populates="question", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="question")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    input = Column(Text)
    expected_output = Column(Text)

    question = relationship("Question", back_populates="test_cases")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    code = Column(Text)
    compile_error = Column(Text, default="")
    warnings = Column(Text, default="")
    all_tests_passed = Column(Boolean, nullable=True)
    error_category = Column(String, default="")
    pedagogical_diagnosis = Column(Text, default="")
    actionable_feedback = Column(Text, default="")
    submitted_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="submissions")
    test_results = relationship("SubmissionTestResult", back_populates="submission", cascade="all, delete-orphan")


class SubmissionTestResult(Base):
    __tablename__ = "submission_test_results"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    input = Column(Text)
    expected_output = Column(Text)
    actual_output = Column(Text)
    passed = Column(Boolean)

    submission = relationship("Submission", back_populates="test_results")
